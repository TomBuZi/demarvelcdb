"""CLI: Bogen-Scans -> Karten-Crops -> Tesseract-OCR -> Review-Artefakte
und konsolidiertes JSON im zzorba-Schema.

v2-Pipeline pro Karte:
  1. Auto-Detect der Karten-Bbox auf dem Bogen (`auto_detect_card_boxes`)
  2. Orientierung bestimmen (`orient.detect`) — probiert 4 Rotationen,
     liefert die mit auflösbarem Set-Indikator + Card-Code + Type-Code zurück
  3. Karte in die ermittelte Orientierung drehen
  4. Pro `type_code` zwei Crops ziehen: `title` (für `name`) und `body`
     (für die spätere Content-Splittung)
  5. Body mit `pytesseract.image_to_data` Zeile für Zeile OCR-en und
     via `sections.split_sections` in traits/text/flavor zerlegen
  6. Ergebnis als parsed.json + Crops im Review-Verzeichnis ablegen

Aufruf:
    python extract.py --pack hood
    python extract.py --pack hood --consolidate
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
import yaml
from PIL import Image

import pytesseract

import tess_setup  # noqa: F401 — setzt Tesseract-Pfad und TESSDATA_PREFIX
import mapping
import orient
import postprocess
import sections as sections_mod

LOG = logging.getLogger("extract")


# Layout-Templates pro Card-Type-Klasse. Werte sind relativ (0..1) zur Karte
# in der Indikator-Orientierung (also dem, was `orient.detect` liefert).
#
# `title` und `body` definieren je ein Rechteck (y_top/y_bottom/x_left/x_right).
# `title_rotate` ist die Vorrotation des Title-Crops in Grad gegen Uhrzeigersinn,
# bevor er an Tesseract geht — bei Anhängen steht der Titel um 90° gedreht
# auf der linken Kante; mit 90° CW (= 270° CCW) wird die Schrift horizontal.
_PORTRAIT_LAYOUT = {
    "title": {"y_top": 0.04, "y_bottom": 0.10, "x_left": 0.03, "x_right": 0.93},
    # y_top=0.50 fängt die Trait-Zeile zuverlässig (sitzt typisch zwischen
    # Illustrationsende und Textbox-Anfang). Der `_trait_match`-Filter in
    # `sections.py` überspringt 1-3 illustrationsbedingte Müll-Zeilen, bevor
    # er aufgibt — daher ist das großzügige y_top gefahrlos.
    "body":  {"y_top": 0.50, "y_bottom": 0.93, "x_left": 0.065, "x_right": 0.92},
    "title_rotate": 0,
}
_ATTACHMENT_LAYOUT = {
    "title": {"y_top": 0.05, "y_bottom": 0.92, "x_left": 0.02, "x_right": 0.15},
    # Body fängt knapp neben der Title-Leiste an. Stat-Boxen liegen darüber
    # bei kleinerem y und werden durch y_top=0.40 ausgeschlossen.
    "body":  {"y_top": 0.50, "y_bottom": 0.92, "x_left": 0.18, "x_right": 0.95},
    "title_rotate": 270,  # 90° im Uhrzeigersinn — gedrehte Schrift wird horizontal
}
# Hauptpläne und Nebenpläne sind beide "Querformat im Druck", aber Titel
# und Textbox sitzen an unterschiedlichen Stellen. Daher zwei getrennte
# Templates — initial mit den gleichen Werten, individuell anpassbar.
_MAIN_SCHEME_LAYOUT = {
    "title": {"y_top": 0.061, "y_bottom": 0.175, "x_left": 0.045, "x_right": 0.89},
    "body":  {"y_top": 0.245, "y_bottom": 0.93, "x_left": 0.05, "x_right": 0.6},
    "title_rotate": 0,
}
_SIDE_SCHEME_LAYOUT = {
    "title": {"y_top": 0.07, "y_bottom": 0.165, "x_left": 0.28, "x_right": 0.95},
    "body":  {"y_top": 0.24, "y_bottom": 0.88, "x_left": 0.445, "x_right": 0.95},
    "title_rotate": 0,
}

TYPE_LAYOUTS: dict[str, dict] = {
    "villain":     _PORTRAIT_LAYOUT,
    "minion":      _PORTRAIT_LAYOUT,
    "treachery":   _PORTRAIT_LAYOUT,
    "environment": _PORTRAIT_LAYOUT,
    "obligation":  _PORTRAIT_LAYOUT,
    "ally":        _PORTRAIT_LAYOUT,
    "attachment":  _ATTACHMENT_LAYOUT,
    "main_scheme": _MAIN_SCHEME_LAYOUT,
    "side_scheme": _SIDE_SCHEME_LAYOUT,
}
DEFAULT_LAYOUT = _PORTRAIT_LAYOUT


@dataclass
class CardEntry:
    code: str | None = None
    name: str = ""
    text: str = ""
    traits: str = ""
    flavor: str = ""
    set_indicator_raw: str = ""
    set_code: str | None = None
    set_position: int | None = None
    type_code: str | None = None
    rotation: int = 0
    deskew_angle: float = 0.0
    sheet: str = ""
    row: int = 0
    col: int = 0
    notes: list[str] = field(default_factory=list)


def load_layout(pack: str) -> dict:
    layout_path = Path(__file__).parent / "layouts" / f"{pack}.yaml"
    with layout_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def preprocess_for_ocr(img_bgr: np.ndarray) -> np.ndarray:
    """Graustufen + ggf. Invertierung + adaptiver Threshold + 2x Resize fürs OCR."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    if gray.mean() < 127:
        gray = cv2.bitwise_not(gray)
    h, w = gray.shape
    gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )


def ocr_text(img_bgr: np.ndarray, psm: int) -> str:
    pre = preprocess_for_ocr(img_bgr)
    return pytesseract.image_to_string(Image.fromarray(pre), lang="deu", config=f"--psm {psm}")


def crop_relative(img: np.ndarray, region: dict) -> np.ndarray:
    h, w = img.shape[:2]
    y1 = int(region["y_top"] * h)
    y2 = int(region["y_bottom"] * h)
    x1 = int(region["x_left"] * w)
    x2 = int(region["x_right"] * w)
    return img[y1:y2, x1:x2]


def _draw_zone(img: np.ndarray, region: dict, color: tuple, label: str) -> None:
    """Zeichnet ein farbiges Rechteck und ein Label inplace auf `img`."""
    h, w = img.shape[:2]
    p1 = (int(region["x_left"] * w), int(region["y_top"] * h))
    p2 = (int(region["x_right"] * w), int(region["y_bottom"] * h))
    cv2.rectangle(img, p1, p2, color, max(2, w // 200))
    # Label oben links innerhalb des Rechtecks.
    cv2.putText(
        img, label, (p1[0] + 8, p1[1] + 32),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, max(1, w // 400),
    )


def draw_zones(card_img: np.ndarray, type_layout: dict, indicator_strip: dict) -> np.ndarray:
    """Liefert eine Kopie des Karten-Bilds mit eingezeichneten Region-Boxen:
    grün=Title, rot=Body, gelb=Indikator-Strip.
    """
    out = card_img.copy()
    _draw_zone(out, type_layout["title"], (0, 200, 0), "TITLE")
    _draw_zone(out, type_layout["body"], (0, 0, 220), "BODY")
    _draw_zone(out, indicator_strip, (0, 220, 220), "INDICATOR")
    return out


def render_attempt_image(
    card_img_in_indicator_orientation: np.ndarray,
    indicator_strip: dict,
    attempt: "orient.IndicatorAttempt",
) -> np.ndarray:
    """Rendert für einen Indikator-OCR-Versuch ein Diagnose-Bild: die Karte
    in der probierten Rotation mit dem gelben Indikator-Strip-Rahmen, plus
    einem Banner oben, der die Rotation, den Roh-OCR-Output und das Parse-
    Resultat zeigt. Damit kann der User für jede unresolved Karte alle 4
    Rotations-Versuche nebeneinander ansehen.
    """
    out = card_img_in_indicator_orientation.copy()
    h, w = out.shape[:2]

    # Strip-Rahmen einzeichnen (gelb, etwas dicker für Sichtbarkeit).
    _draw_zone(out, indicator_strip, (0, 220, 220), "INDICATOR")

    # Banner oben anhängen.
    banner_h = max(180, w // 8)
    banner = np.full((banner_h, w, 3), 245, dtype=np.uint8)
    composite = np.vstack([banner, out])

    # Text auf den Banner schreiben.
    font = cv2.FONT_HERSHEY_SIMPLEX
    base_scale = max(0.6, w / 1500)
    line_h = int(36 * base_scale)
    y = line_h

    def put(line: str, color=(0, 0, 0), bold: bool = False) -> None:
        nonlocal y
        thickness = max(1, int(2 * base_scale)) + (1 if bold else 0)
        cv2.putText(composite, line, (16, y), font, base_scale, color, thickness)
        y += line_h

    resolved = attempt.resolved_code is not None
    status_color = (0, 130, 0) if resolved else (0, 0, 200)
    status = "RESOLVED" if resolved else "NOT RESOLVED"
    # Hershey-Font in cv2.putText kennt kein Unicode — `°` und `—` würden als
    # `?` rendern. Wir benutzen reine ASCII-Glyphen im Banner.
    put(f"Rotation {attempt.rotation_deg} deg  -  {status}", status_color, bold=True)

    # Roh-OCR auf maximal 2 Zeilen mitnehmen.
    raw = attempt.raw_text.replace("\n", " | ")
    max_chars = max(40, w // int(15 * base_scale))
    raw1 = raw[:max_chars]
    raw2 = raw[max_chars : 2 * max_chars]
    put(f"OCR: {raw1}")
    if raw2:
        put(f"     {raw2}")

    set_part = attempt.parsed_set_name or "(leer)"
    pos_part = str(attempt.parsed_position) if attempt.parsed_position is not None else "-"
    code_part = attempt.resolved_set_code or "-"
    card_part = attempt.resolved_code or "-"
    put(f"parsed: name='{set_part[:40]}'  pos={pos_part}  set_code={code_part}  code={card_part}")
    return composite


def deskew_card(
    card_img: np.ndarray,
    *,
    bg_threshold: int = 240,
    min_area_frac: float = 0.5,
    angle_tolerance_deg: float = 0.3,
) -> tuple[np.ndarray, float]:
    """Erkennt die tatsächliche Schräglage einer Karte innerhalb ihres
    Auto-Detect-Crops und rotiert sie auf 0°.

    Verfahren: Threshold gegen den weißen Hintergrund → größte Kontur als
    Karte → `cv2.minAreaRect` liefert (Center, Size, Winkel). Der Winkel
    wird auf [-45, 45] normalisiert; ist er kleiner als `angle_tolerance_deg`,
    wird gar nicht rotiert (kein Pixel-Verlust durch unnötigen Resample).
    Nach der Rotation wird die Karte auf ihren neuen axis-aligned BBox tight
    gecroppt — so verschwinden auch die weißen Dreiecke an den Ecken.

    Liefert (deskewed_img, angle_deg). `angle_deg` ist die angewendete
    Rotation; 0.0 wenn nichts gedreht wurde.
    """
    H, W = card_img.shape[:2]
    gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, bg_threshold, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return card_img, 0.0
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < min_area_frac * H * W:
        return card_img, 0.0

    rect = cv2.minAreaRect(largest)
    angle = float(rect[-1])
    # Normalisierung auf (-45, 45] — funktioniert über alle OpenCV-Versionen.
    while angle > 45:
        angle -= 90
    while angle <= -45:
        angle += 90

    if abs(angle) < angle_tolerance_deg:
        return card_img, 0.0

    # Rotation um die Bildmitte; weißer Rand füllt entstehende Ecken.
    M = cv2.getRotationMatrix2D((W / 2, H / 2), angle, 1.0)
    rotated = cv2.warpAffine(
        card_img, M, (W, H),
        flags=cv2.INTER_CUBIC,
        borderValue=(255, 255, 255),
    )

    # Nach der Rotation Karte erneut finden und tight croppen — vermeidet
    # weiße Dreiecke an den Ecken, die das spätere Auto-Invert verfälschen.
    gray2 = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    _, mask2 = cv2.threshold(gray2, bg_threshold, 255, cv2.THRESH_BINARY_INV)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
    contours2, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours2:
        largest2 = max(contours2, key=cv2.contourArea)
        x, y, w2, h2 = cv2.boundingRect(largest2)
        rotated = rotated[y : y + h2, x : x + w2]

    return rotated, angle


def auto_detect_card_boxes(
    sheet_img: np.ndarray,
    *,
    bg_threshold: int = 240,
    min_area_frac: float = 0.02,
    morph_kernel: int = 15,
) -> list[tuple[int, int, int, int]]:
    """Findet einzelne Karten-Bounding-Boxes auf einem Bogen mit klarem
    weißen Hintergrund. Liefert Liste von (x, y, w, h), bereits sortiert in
    Lese-Reihenfolge (oben-links → unten-rechts).
    """
    H, W = sheet_img.shape[:2]
    sheet_area = W * H

    gray = cv2.cvtColor(sheet_img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, bg_threshold, 255, cv2.THRESH_BINARY_INV)
    if morph_kernel > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel, morph_kernel))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: list[tuple[int, int, int, int]] = []
    min_area = sheet_area * min_area_frac
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h < min_area or w < 200 or h < 200:
            continue
        boxes.append((x, y, w, h))

    if not boxes:
        return []

    median_h = int(np.median([h for *_, h in boxes]))
    row_tolerance = max(median_h // 2, 100)

    boxes_with_centers = sorted(((y + h // 2, x + w // 2, x, y, w, h) for x, y, w, h in boxes), key=lambda t: t[0])
    rows: list[list[tuple[int, int, int, int, int, int]]] = []
    current_row: list = []
    current_y_anchor: int | None = None
    for entry in boxes_with_centers:
        cy = entry[0]
        if current_y_anchor is None or abs(cy - current_y_anchor) <= row_tolerance:
            current_row.append(entry)
            current_y_anchor = cy if current_y_anchor is None else (current_y_anchor + cy) // 2
        else:
            rows.append(current_row)
            current_row = [entry]
            current_y_anchor = cy
    if current_row:
        rows.append(current_row)

    ordered: list[tuple[int, int, int, int]] = []
    for r in rows:
        for _, _, x, y, w, h in sorted(r, key=lambda t: t[1]):
            ordered.append((x, y, w, h))
    return ordered


def _build_card_iter(sheet_img: np.ndarray, sheet_layout: dict):
    """Yields (row, col, card_img) tuples — entweder aus dem festen Grid
    oder aus Auto-Detection.
    """
    if sheet_layout.get("auto_detect"):
        boxes = auto_detect_card_boxes(sheet_img)
        cols_hint = sheet_layout.get("cols", 3)
        for idx, (x, y, w, h) in enumerate(boxes):
            row, col = divmod(idx, cols_hint)
            yield row, col, sheet_img[y : y + h, x : x + w]
        return

    for card_def in sheet_layout.get("cards", []):
        row = int(card_def["row"])
        col = int(card_def["col"])
        x = sheet_layout["origin_x"] + col * (sheet_layout["card_w"] + sheet_layout["gap_x"])
        y = sheet_layout["origin_y"] + row * (sheet_layout["card_h"] + sheet_layout["gap_y"])
        yield row, col, sheet_img[y : y + sheet_layout["card_h"], x : x + sheet_layout["card_w"]]


def process_card(
    card_img: np.ndarray,
    pack_mapper: mapping.PackMapper,
    sheet_name: str,
    row: int,
    col: int,
    slot_dir: Path,
    *,
    visualize_only: bool = False,
) -> CardEntry:
    """Pipeline für eine einzelne Karte.

    Schritte:
      1. Deskew des Auto-Detect-Crops (kleine Scan-Schräglagen rausrechnen)
      2. 4-Rotationen-Indikator-OCR → (rotation, code, type_code)
      3. Karte in Indikator-Orientierung drehen
      4. Title- und Body-Region nach Type-Layout cropen
      5. Im Normal-Modus: Title-OCR + Body-Zeilen-OCR + Section-Split
         Im Visualize-Modus: nur Zonen aufs Bild zeichnen, kein Body-OCR

    Schreibt Crops + parsed.json in `slot_dir`.
    """
    regions_dir = slot_dir / "regions"
    regions_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(slot_dir / "cropped_raw.png"), card_img)

    # 1) Deskew: Karte exakt auf 0° ausrichten.
    deskewed, deskew_angle = deskew_card(card_img)
    if deskew_angle != 0.0:
        cv2.imwrite(str(slot_dir / "cropped_deskewed.png"), deskewed)

    # 2) Orientierung über 4 Rotationen ermitteln. `attempts` enthält für
    # jede Rotation Roh-OCR + Parse-Resultate (für Diagnose unresolved Karten).
    orientation, attempts = orient.detect(deskewed, pack_mapper)
    oriented = orient.rotate(deskewed, orientation.rotation_deg)
    cv2.imwrite(str(slot_dir / "cropped.png"), oriented)

    # 3) Type-Layout wählen.
    layout = TYPE_LAYOUTS.get(orientation.type_code or "", DEFAULT_LAYOUT)

    notes: list[str] = []
    if not orientation.is_resolved:
        notes.append(
            f"Orientierung/Code nicht aufgelöst: rotation={orientation.rotation_deg}°, "
            f"indicator_raw={orientation.indicator_raw!r}, set_code={orientation.set_code}, "
            f"set_position={orientation.set_position}"
        )

    if visualize_only:
        # zones.png zeichnet den Type-spezifischen Indikator-Strip — also
        # genau den, den der User für die erkannte Type-Klasse eingestellt hat
        # (Fallback `_default` wenn kein Eintrag oder Type unbekannt).
        zones_strip = orient.indicator_strip_for(orientation.type_code)
        zones_img = draw_zones(oriented, layout, zones_strip)
        cv2.imwrite(str(slot_dir / "zones.png"), zones_img)

        # Für unresolved Karten: alle Versuche als annotiertes Bild + JSON.
        # Mit Strip-Varianten gibt es nun (Rotation × Strip-Key)-Kombinationen;
        # identische Strip-Werte werden visuell allerdings auf eine Datei pro
        # Rotation zusammengefasst (siehe Filename-Schema).
        if not orientation.is_resolved:
            attempts_summary = []
            seen_filenames: set[str] = set()
            for att in attempts:
                strip = orient.INDICATOR_STRIPS.get(att.strip_key, orient.INDICATOR_STRIP)
                rotated_for_attempt = orient.rotate(deskewed, att.rotation_deg)
                attempt_img = render_attempt_image(rotated_for_attempt, strip, att)
                fname = f"attempt_{att.rotation_deg:03d}deg_{att.strip_key}.png"
                # Wenn mehrere Strip-Keys identisch sind (Initialzustand),
                # entstehen mehrere Files mit demselben Inhalt — das stört nicht
                # und macht später beim Tunen klar, welcher Key was darstellt.
                cv2.imwrite(str(slot_dir / fname), attempt_img)
                seen_filenames.add(fname)
                attempts_summary.append({
                    "rotation_deg": att.rotation_deg,
                    "strip_key": att.strip_key,
                    "raw_text": att.raw_text,
                    "parsed_set_name": att.parsed_set_name,
                    "parsed_position": att.parsed_position,
                    "resolved_set_code": att.resolved_set_code,
                    "resolved_code": att.resolved_code,
                })
            (slot_dir / "attempts.json").write_text(
                json.dumps(attempts_summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        entry = CardEntry(
            code=orientation.code,
            set_indicator_raw=orientation.indicator_raw,
            set_code=orientation.set_code,
            set_position=orientation.set_position,
            type_code=orientation.type_code,
            rotation=orientation.rotation_deg,
            deskew_angle=deskew_angle,
            sheet=sheet_name,
            row=row,
            col=col,
            notes=notes,
        )
        parsed = {
            "code": entry.code,
            "set_code": entry.set_code,
            "set_position": entry.set_position,
            "type_code": entry.type_code,
            "rotation": entry.rotation,
            "deskew_angle": round(entry.deskew_angle, 2),
            "set_indicator_raw": entry.set_indicator_raw,
            "applied_layout": orientation.type_code or "(default=portrait)",
            "sheet": entry.sheet,
            "row": entry.row,
            "col": entry.col,
            "notes": entry.notes,
        }
        (slot_dir / "parsed.json").write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return entry

    # 4) Title-Crop + ggf. Vorrotation, dann OCR.
    title_img = crop_relative(oriented, layout["title"])
    if layout.get("title_rotate"):
        title_img = orient.rotate(title_img, layout["title_rotate"])
    cv2.imwrite(str(regions_dir / "title.png"), title_img)
    title_raw = ocr_text(title_img, psm=7)
    (regions_dir / "title.txt").write_text(title_raw, encoding="utf-8")
    name = postprocess.finalize_name(title_raw)

    # 5) Body-Crop, Zeilen-OCR, content-basiertes Splitting.
    body_img = crop_relative(oriented, layout["body"])
    cv2.imwrite(str(regions_dir / "body.png"), body_img)
    body_pre = preprocess_for_ocr(body_img)
    cv2.imwrite(str(regions_dir / "body_preprocessed.png"), body_pre)
    lines = sections_mod.ocr_lines(body_pre, psm=6)
    (regions_dir / "body_lines.txt").write_text(
        "\n".join(f"[{l.x},{l.y},{l.w}x{l.h}] {l.text}" for l in lines),
        encoding="utf-8",
    )
    split = sections_mod.split_sections(
        lines, body_pre.shape[1], type_code=orientation.type_code,
    )

    entry = CardEntry(
        code=orientation.code,
        name=name,
        text=split["text"],
        traits=split["traits"],
        flavor=split["flavor"],
        set_indicator_raw=orientation.indicator_raw,
        set_code=orientation.set_code,
        set_position=orientation.set_position,
        type_code=orientation.type_code,
        rotation=orientation.rotation_deg,
        deskew_angle=deskew_angle,
        sheet=sheet_name,
        row=row,
        col=col,
        notes=notes,
    )

    parsed = {
        "code": entry.code,
        "name": entry.name,
        "text": entry.text,
        "traits": entry.traits,
        "flavor": entry.flavor,
        "set_code": entry.set_code,
        "set_position": entry.set_position,
        "type_code": entry.type_code,
        "rotation": entry.rotation,
        "deskew_angle": round(entry.deskew_angle, 2),
        "set_indicator_raw": entry.set_indicator_raw,
        "sheet": entry.sheet,
        "row": entry.row,
        "col": entry.col,
        "notes": entry.notes,
    }
    (slot_dir / "parsed.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return entry


def process_sheet(
    pack: str,
    sheet_path: Path,
    sheet_layout: dict,
    review_dir: Path,
    pack_mapper: mapping.PackMapper,
    *,
    visualize_only: bool = False,
) -> list[CardEntry]:
    LOG.info("Verarbeite Bogen: %s", sheet_path.name)
    sheet_img = cv2.imdecode(
        np.fromfile(str(sheet_path), dtype=np.uint8), cv2.IMREAD_COLOR
    )
    if sheet_img is None:
        LOG.error("Bogen %s konnte nicht geladen werden", sheet_path)
        return []

    entries: list[CardEntry] = []
    for row, col, card_img in _build_card_iter(sheet_img, sheet_layout):
        slot_dir = review_dir / sheet_path.stem / f"{row}_{col}"
        entries.append(
            process_card(
                card_img, pack_mapper, sheet_path.name, row, col, slot_dir,
                visualize_only=visualize_only,
            )
        )
    return entries


def cmd_extract(args: argparse.Namespace) -> int:
    pack = args.pack
    layout = load_layout(pack)
    scans_dir = Path(args.scans_dir)
    review_dir = Path(__file__).parent / "output" / "review" / pack
    review_dir.mkdir(parents=True, exist_ok=True)

    pack_mapper = mapping.PackMapper(pack)
    LOG.info("Lade englisches Pack-JSON für '%s'", pack)
    pack_mapper.load()

    sheet_keys = [k for k in layout.keys() if k not in ("defaults", "regions")]
    if not sheet_keys:
        LOG.error("Keine Bögen in layouts/%s.yaml definiert", pack)
        return 1

    # `--sheet`-Filter für schnelle Iteration auf einem einzelnen Bogen.
    if args.sheet:
        wanted = set(args.sheet)
        before = list(sheet_keys)
        sheet_keys = [k for k in sheet_keys if k in wanted]
        if not sheet_keys:
            LOG.error(
                "Kein Bogen-Match für --sheet=%s. Verfügbar: %s",
                ", ".join(args.sheet), ", ".join(before),
            )
            return 1
        LOG.info("Bogen-Filter aktiv: nur %s", ", ".join(sheet_keys))

    all_entries: list[CardEntry] = []
    for sheet_key in sheet_keys:
        sheet_path = scans_dir / sheet_key
        if not sheet_path.exists():
            LOG.warning("Bogen-Datei fehlt: %s", sheet_path)
            continue
        sheet_layout = layout[sheet_key]
        all_entries.extend(
            process_sheet(
                pack, sheet_path, sheet_layout, review_dir, pack_mapper,
                visualize_only=args.visualize,
            )
        )

    if args.visualize:
        # Aktuelle Layout-Werte rauspusten, damit sie der User editieren kann.
        layouts_path = Path(__file__).parent / "output" / f"{pack}_layouts.json"
        layouts_dump = {
            "indicator_strips": orient.INDICATOR_STRIPS,
            "type_layouts": TYPE_LAYOUTS,
            "_note": (
                "Werte sind relative Anteile [0..1] der Karten-Dimensionen "
                "in der Indikator-Orientierung. Editiere TYPE_LAYOUTS in "
                "extract.py bzw. INDICATOR_STRIPS in orient.py, um Anpassungen "
                "wirksam zu machen. INDICATOR_STRIPS-Schlüssel: '_default' für "
                "alle Hochformat-Karten, plus optional 'attachment', "
                "'main_scheme', 'side_scheme' für Type-spezifische Tunings."
            ),
        }
        layouts_path.write_text(
            json.dumps(layouts_dump, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        resolved = sum(1 for e in all_entries if e.code)
        LOG.info(
            "Visualisierung fertig: %d Karten, %d mit Type erkannt. "
            "Pro Slot: zones.png + cropped.png + cropped_deskewed.png. "
            "Layouts geschrieben nach %s — bitte prüfen und ggf. die "
            "Konstanten in extract.py:TYPE_LAYOUTS / orient.py:INDICATOR_STRIP anpassen.",
            len(all_entries),
            resolved,
            layouts_path,
        )
    else:
        resolved = sum(1 for e in all_entries if e.code)
        LOG.info(
            "OCR fertig: %d Karten in %s — %d mit Code aufgelöst, %d für manuelles Review.",
            len(all_entries),
            review_dir,
            resolved,
            len(all_entries) - resolved,
        )
    return 0


def cmd_consolidate(args: argparse.Namespace) -> int:
    pack = args.pack
    review_dir = Path(__file__).parent / "output" / "review" / pack
    if not review_dir.exists():
        LOG.error("Kein Review-Verzeichnis %s — vorher --extract laufen lassen.", review_dir)
        return 1

    parsed_files = sorted(review_dir.glob("*/*/parsed.json"))
    if not parsed_files:
        LOG.error("Keine parsed.json-Dateien in %s gefunden.", review_dir)
        return 1

    consolidated: list[dict] = []
    skipped: list[str] = []
    seen_codes: set[str] = set()

    for pf in parsed_files:
        try:
            data = json.loads(pf.read_text(encoding="utf-8"))
        except Exception as e:
            LOG.warning("Kann %s nicht lesen: %s", pf, e)
            skipped.append(str(pf))
            continue

        code = data.get("code")
        if not code:
            skipped.append(f"{pf} (kein code)")
            continue
        if code in seen_codes:
            LOG.info("Doppelter code %s übersprungen (%s)", code, pf)
            continue
        seen_codes.add(code)

        entry: dict = {"code": code}
        for f in ("name", "text", "traits", "flavor", "subname"):
            v = data.get(f)
            if v:
                entry[f] = v
        consolidated.append(entry)

    out_path = Path(__file__).parent / "output" / f"{pack}_encounter.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(consolidated, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    LOG.info("Geschrieben: %s (%d Einträge, %d skipped)", out_path, len(consolidated), len(skipped))
    for s in skipped:
        LOG.info("  skipped: %s", s)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, help="Pack-Code, z.B. 'hood'")
    parser.add_argument(
        "--scans-dir",
        default=r"C:\Repos\Sourcen_Scans\mereel",
        help="Verzeichnis mit den Bogen-Scans",
    )
    parser.add_argument(
        "--consolidate",
        action="store_true",
        help="Aus den parsed.json-Dateien die finale <pack>_encounter.json bauen",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help=(
            "Statt Body-OCR nur Karten ausschneiden, deskewen, Indikator/Type "
            "ermitteln und die Region-Boxen (Title/Body/Indikator) als "
            "zones.png pro Slot rausschreiben. Layout-Koordinaten landen "
            "in output/<pack>_layouts.json zum Anpassen."
        ),
    )
    parser.add_argument(
        "--sheet",
        action="append",
        default=[],
        metavar="DATEI",
        help=(
            "Nur diesen Bogen verarbeiten (Dateiname wie in layouts/<pack>.yaml, "
            "z.B. 'HoodSetGER_4.jpg'). Mehrfach angeben für mehrere Bögen. "
            "Ohne Flag werden alle Bögen verarbeitet."
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.consolidate:
        return cmd_consolidate(args)
    return cmd_extract(args)


if __name__ == "__main__":
    sys.exit(main())
