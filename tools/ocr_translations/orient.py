"""Orientierungs-Detektor für einzelne Karten-Crops.

Karten liegen auf den Bögen in unterschiedlichen Rotationen (Standard-Hochformat,
Anhang, Scheme), und je nach Scan auch noch um 180° gedreht oder andersherum
gespiegelt. Wir probieren alle vier 90°-Rotationen und identifizieren diejenige,
in der ein parseable Set-Indikator (`XXX (n/m)`) am unteren Rand auftaucht.

Sobald ein Indikator zur Position passt und sich darüber ein `code` aus dem
englischen Pack-JSON ableiten lässt, ist die Orientierung eindeutig. Aus
demselben Card-Eintrag ziehen wir auch den `type_code`, der in der Pipeline
das Region-Template auswählt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image
import pytesseract

import tess_setup  # noqa: F401 — setzt Tesseract-Pfad und TESSDATA_PREFIX
import mapping

# Reihenfolge der Rotationen — 0° zuerst, weil das der häufigste Fall ist.
# 180° ist nie nötig: Karten liegen auf den Bögen entweder hochkant (0°),
# um 90° CCW oder um 90° CW gedreht. Nichts kommt kopfüber, also lassen wir
# das aus — spart 25 % OCR pro Karte.
ROTATIONS = (0, 90, 270)

# Indikator-Streifen — pro Type-Klasse einstellbar. Das Henne-Ei-Problem
# (welcher Type? wir wissen es ja erst nach dem Indikator-OCR) löst `detect()`,
# indem es alle Varianten ausprobiert und die mit auflösbarem Code gewinnen
# lässt. Bei der Visualisierung wird dann aber der Streifen der **erkannten
# Type-Klasse** gezeichnet — nicht der, der zufällig das richtige Resultat
# geliefert hat — damit der User die per-Type-Tuning-Kontrolle behält.
INDICATOR_STRIPS: dict[str, dict] = {
    "_default":    {"y_top": 0.93, "y_bottom": 1.0, "x_left": 0.0, "x_right": 1.0},
    "attachment":  {"y_top": 0.92, "y_bottom": 1.0, "x_left": 0.0, "x_right": 1.0},
    "main_scheme": {"y_top": 0.875, "y_bottom": 1.0, "x_left": 0.6, "x_right": 1.0},
    "side_scheme": {"y_top": 0.878, "y_bottom": 1.0, "x_left": 0.476, "x_right": 1.0},
}

# Backward-Compat-Alias für Code, der den alten Singular-Namen erwartet.
INDICATOR_STRIP = INDICATOR_STRIPS["_default"]


def indicator_strip_for(type_code: str | None) -> dict:
    """Liefert den Streifen, der für die gegebene Type-Klasse gezeichnet
    werden soll — fällt auf `_default` zurück, wenn nichts spezifisches
    eingetragen ist (oder der Type unbekannt ist).
    """
    if type_code and type_code in INDICATOR_STRIPS:
        return INDICATOR_STRIPS[type_code]
    return INDICATOR_STRIPS["_default"]


@dataclass
class Orientation:
    rotation_deg: int
    strip_key: str
    indicator_raw: str
    set_code: str | None
    set_position: int | None
    code: str | None
    type_code: str | None

    @property
    def is_resolved(self) -> bool:
        return self.code is not None


@dataclass
class IndicatorAttempt:
    """Diagnose-Datensatz pro (Rotation, Strip-Variante)."""
    rotation_deg: int
    strip_key: str
    raw_text: str
    parsed_set_name: str
    parsed_position: int | None
    resolved_set_code: str | None
    resolved_code: str | None


def rotate(img: np.ndarray, deg: int) -> np.ndarray:
    """Rotation gegen den Uhrzeigersinn um Vielfache von 90°."""
    if deg % 360 == 0:
        return img
    if deg % 360 == 90:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if deg % 360 == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    if deg % 360 == 270:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    raise ValueError(f"Nur 0/90/180/270 Grad unterstützt, bekam {deg}")


def _crop_relative(img: np.ndarray, region: dict) -> np.ndarray:
    h, w = img.shape[:2]
    y1 = int(region["y_top"] * h)
    y2 = int(region["y_bottom"] * h)
    x1 = int(region["x_left"] * w)
    x2 = int(region["x_right"] * w)
    return img[y1:y2, x1:x2]


def _preprocess_strip(img_bgr: np.ndarray) -> np.ndarray:
    """Sehr leichtes Preprocessing: Graustufen, ggf. Invertierung des hellen
    Texts auf dunklem Banner, 2× Resize. Ein adaptiver Threshold würde bei
    schmalen Streifen mit mehreren Helligkeitsbereichen (Border, Banner,
    Karten-Art) den Text zerstören — Tesseract macht intern eine eigene
    Binarisierung, die hier zuverlässiger ist.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    if gray.mean() < 127:
        gray = cv2.bitwise_not(gray)
    h, w = gray.shape
    return cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)


# Indikator-Pattern wie "(1/16)" — wird genutzt, um zu entscheiden, ob ein
# OCR-Output verwertbar ist. Wenn das preprocessed Bild den Pattern nicht
# liefert, fallen wir auf raw color zurück.
_INDICATOR_PATTERN_RE = re.compile(r"\(\s*\d+\s*[/\\]\s*\d+\s*\)")


def _ocr_indicator(strip_bgr: np.ndarray) -> str:
    """OCR auf den Indikator-Streifen mit Preprocessing+Fallback-Kaskade.

    1. Versuch: gray (+ Auto-Invert) + 2× Resize, PSM 11. Funktioniert bei
       den meisten Karten zuverlässig.
    2. Wenn Output kein `(n/m)`-Pattern enthält, zweite Runde direkt auf
       raw color: bei manchen Karten zerstört das Preprocessing die feinen
       Strukturen, raw color liefert dann die Lesung.

    PSM 11 (sparse text) ist hier robuster als PSM 7, weil bei Schemes/
    Attachments der Indikator schmal neben Copyright/Illustrator-Text steht.
    """
    pre = _preprocess_strip(strip_bgr)
    text = pytesseract.image_to_string(Image.fromarray(pre), lang="deu", config="--psm 11")
    if _INDICATOR_PATTERN_RE.search(text):
        return text
    # Fallback: raw color
    raw_text = pytesseract.image_to_string(
        Image.fromarray(strip_bgr), lang="deu", config="--psm 11",
    )
    if _INDICATOR_PATTERN_RE.search(raw_text):
        return raw_text
    # Beide ohne klares Muster: längeren Output zurückgeben (mehr Material
    # für das Set-Name-Matching, falls die Position fehlt).
    return text if len(text.strip()) >= len(raw_text.strip()) else raw_text


def detect(
    card_img: np.ndarray, pack_mapper: mapping.PackMapper
) -> tuple[Orientation, list[IndicatorAttempt]]:
    """Probiert alle 4 Rotationen × alle Strip-Varianten in `INDICATOR_STRIPS`,
    OCR-t den Indikator-Streifen, parst und löst gegen das Pack-JSON auf.
    Liefert die beste Orientierung plus die komplette Diagnose-Liste.

    Strip-Varianten mit identischen Koordinaten werden zu **einer** OCR-
    Operation zusammengefasst; der gleiche Output wird dann unter allen
    matching Schlüsseln in `attempts` eingetragen — so bleibt der Lauf
    schnell, solange der User die Strips nicht aktiv per Type tuned hat.

    Wenn keine Variante einen verwertbaren Indikator liefert, fällt die
    Funktion auf Rotation 0° + `_default`-Strip zurück.
    """
    attempts: list[IndicatorAttempt] = []
    candidates: list[Orientation] = []

    # Strip-Varianten nach ihren Koordinaten gruppieren — gleiche Koordinaten
    # = ein OCR-Lauf, dann unter allen Schlüsseln aufgezeichnet.
    grouped: dict[tuple, list[str]] = {}
    for key, strip in INDICATOR_STRIPS.items():
        sig = (strip["y_top"], strip["y_bottom"], strip["x_left"], strip["x_right"])
        grouped.setdefault(sig, []).append(key)

    for deg in ROTATIONS:
        rotated = rotate(card_img, deg)
        for sig, keys in grouped.items():
            strip = INDICATOR_STRIPS[keys[0]]
            text = _ocr_indicator(_crop_relative(rotated, strip))
            set_name, position = mapping.PackMapper.parse_set_indicator(text)
            set_code = pack_mapper.resolve_set_code(set_name) if set_name else None

            # Zwei parallele Auflösungs-Wege:
            #   a) klassisch: (n/m)-Indikator + Set-Name → Position-Lookup
            #   b) Suffix unten rechts (`4A`, `4B`, `13`) → direkter Code-Lookup
            #
            # Position gewinnt grundsätzlich (robust gegen OCR-Müll, der
            # zufällig wie ein Suffix aussieht). Suffix nur, wenn er die A/B-
            # Schwester der position-gefundenen Karte trifft — dann sind wir
            # auf der gegenüberliegenden Seite. Wenn Position GAR NICHTS liefert
            # (z.B. bei B-Seiten ohne `(n/m)`), fällt Suffix als Notnagel ein.
            position_code = (
                pack_mapper.find_code(set_code, position)
                if set_code and position is not None
                else None
            )
            suffix = mapping.PackMapper.parse_card_suffix(text)
            suffix_code = pack_mapper.find_code_by_suffix(suffix) if suffix else None

            code = position_code
            if position_code and suffix_code and position_code != suffix_code:
                p_low = position_code.lower()
                s_low = suffix_code.lower()
                if (
                    len(p_low) == len(s_low)
                    and p_low[:-1] == s_low[:-1]
                    and p_low[-1] in ("a", "b")
                    and s_low[-1] in ("a", "b")
                ):
                    code = suffix_code
            elif not position_code and suffix_code:
                code = suffix_code

            type_code = pack_mapper.get_type_code(code)
            if code and not set_code:
                card_entry = pack_mapper.get_card(code)
                if card_entry:
                    set_code = card_entry.get("set_code")

            # Falls Position nicht aus dem (n/m)-Indikator kam, hole sie aus
            # dem englischen Card-Eintrag — fürs parsed.json-Diagnostikfeld.
            effective_position = position
            if effective_position is None and code:
                entry = pack_mapper.get_card(code)
                if entry and "set_position" in entry:
                    effective_position = int(entry["set_position"])

            for key in keys:
                attempts.append(
                    IndicatorAttempt(
                        rotation_deg=deg,
                        strip_key=key,
                        raw_text=text.strip(),
                        parsed_set_name=set_name,
                        parsed_position=position,
                        resolved_set_code=set_code,
                        resolved_code=code,
                    )
                )

            # Kandidat nur wenn ein Code aufgelöst wurde — egal über welchen
            # der beiden Wege. Damit kommen B-Seiten via Suffix auch in die
            # Kandidatenliste, obwohl ihnen der `(n/m)`-Indikator fehlt.
            if code is None:
                continue
            preferred_key = type_code if type_code in keys else keys[0]
            orientation = Orientation(
                rotation_deg=deg,
                strip_key=preferred_key,
                indicator_raw=text.strip(),
                set_code=set_code,
                set_position=effective_position,
                code=code,
                type_code=type_code,
            )
            candidates.append(orientation)

            # Short-Circuit auf erstem aufgelöstem Kandidaten — siehe v2.1
            # Performance-Plan.
            return orientation, attempts

    if not candidates:
        return Orientation(0, "_default", "", None, None, None, None), attempts

    candidates.sort(
        key=lambda o: (o.code is not None, o.set_code is not None),
        reverse=True,
    )
    return candidates[0], attempts
