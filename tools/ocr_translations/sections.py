"""Content-basiertes Splitting des Body-Crops einer Karte in
`traits` / `text` / `flavor`.

Idee: statt für jede Karte präzise Region-Grenzen zu pflegen, nehmen wir
einmal eine großzügige Body-Box und lassen Tesseract pro Zeile Bbox + Text
liefern (`image_to_data`). Anhand visueller und textlicher Heuristiken
entscheiden wir dann, was zu welchem Feld gehört:

- **traits** — eine kurze, zentrierte Zeile am Anfang, in Großbuchstaben,
  mit Punkt(en) als Trennzeichen ("KRIMINELLER. SCHLÄGER.").
- **flavor** — ein zusammenhängender Block am Ende, der mit „/" beginnt
  und auf "/" oder einer Zuschreibung "— Name" endet.
- **text** — alles dazwischen.

Felder dürfen leer bleiben — nicht jede Karte hat Traits oder Flavor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
from PIL import Image
import pytesseract

import postprocess


@dataclass
class Line:
    text: str
    x: int
    y: int
    w: int
    h: int
    avg_conf: float


def ocr_lines(body_img_pre: np.ndarray, psm: int = 6) -> list[Line]:
    """Führt Tesseract auf dem vorverarbeiteten Body-Bild aus und liefert
    eine geordnete Liste von Zeilen (Reihenfolge: oben nach unten)."""
    data = pytesseract.image_to_data(
        Image.fromarray(body_img_pre),
        lang="deu",
        config=f"--psm {psm}",
        output_type=pytesseract.Output.DICT,
    )

    grouped: dict[tuple[int, int, int], list[int]] = {}
    n = len(data["text"])
    for i in range(n):
        text = (data["text"][i] or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        if conf < 0:
            continue
        key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
        grouped.setdefault(key, []).append(i)

    lines: list[Line] = []
    for key, indices in grouped.items():
        words = [data["text"][i] for i in indices]
        xs = [int(data["left"][i]) for i in indices]
        ys = [int(data["top"][i]) for i in indices]
        ws = [int(data["width"][i]) for i in indices]
        hs = [int(data["height"][i]) for i in indices]
        confs = [float(data["conf"][i]) for i in indices]
        x = min(xs)
        y = min(ys)
        x_right = max(xs[i] + ws[i] for i in range(len(indices)))
        y_bottom = max(ys[i] + hs[i] for i in range(len(indices)))
        lines.append(
            Line(
                text=" ".join(words),
                x=x,
                y=y,
                w=x_right - x,
                h=y_bottom - y,
                avg_conf=sum(confs) / max(len(confs), 1),
            )
        )
    lines.sort(key=lambda l: (l.y, l.x))
    return lines


# Pattern für eine Trait-Zeile: ein oder mehrere Trait-Tokens, jedes startet
# mit einem Großbuchstaben (auch Umlaut), und endet auf Punkt — oder Komma,
# weil OCR den Punkt häufig als Komma fehl-liest (z.B. "TECH. WAFFE,").
# `finalize_traits` normalisiert das später wieder auf Punkt.
#
# Wir matchen am Zeilenanfang ohne `$`-Anchor, damit OCR-Müll nach dem
# letzten Terminator (z.B. "KRIMINELLER. —", "WAFFE. ı") nicht den Match killt.
_TRAIT_TOKEN = r"[A-ZÄÖÜ][A-ZÄÖÜa-zäöüß]+(?:\s+[A-ZÄÖÜ][A-ZÄÖÜa-zäöüß]+)*"
TRAIT_LINE_RE = re.compile(
    rf"^\s*({_TRAIT_TOKEN}[.,](?:\s+{_TRAIT_TOKEN}[.,])*)"
)

# Eröffnungs- und Schluss-Anführungszeichen, die wir bei deutschen Karten
# erwarten — einschließlich der OCR-typischen ASCII-Variante.
_OPEN_QUOTES = "„\"“"
_CLOSE_QUOTES = "\"”“"

# Lemma-Anfänge, an denen die Spielregel-Effekte beginnen. Wenn vor solch
# einer Zeile ein Block aus Prosa steht (typisch bei Hauptplänen A-Seite),
# ist das die Flavor-Beschreibung des Schemas. `BOLD_LEMMATA` aus postprocess
# ist eine Liste von Regex-Fragmenten, die wir hier zu einem ODER-Pattern
# zusammenfügen.
_LEMMA_START_RE = re.compile(
    r"^\s*(?:<b>)?(" + "|".join(postprocess.BOLD_LEMMATA) + r")\b[\s:.\-]",
    re.IGNORECASE,
)


def _looks_like_lemma_start(text: str) -> bool:
    return bool(_LEMMA_START_RE.match(text))


def _is_centered(line: Line, body_w: int, tolerance_frac: float = 0.12) -> bool:
    line_center = line.x + line.w / 2
    body_center = body_w / 2
    return abs(line_center - body_center) <= body_w * tolerance_frac


def _trait_match(line: Line, body_w: int) -> str | None:
    """Liefert den extrahierten Trait-String, falls die Zeile als Trait-Zeile
    durchgeht — sonst None. Trait-Zeilen sind zentriert, fangen mit
    Großbuchstaben an und enden auf Punkt; nach dem letzten Punkt darf nur
    sehr wenig OCR-Müll stehen. Centering ist großzügig toleriert, weil
    Multi-Trait-Zeilen wie "KRIMINELLER. MASTERS OF EVIL." sehr lang werden.
    """
    m = TRAIT_LINE_RE.match(line.text)
    if not m:
        return None
    matched = m.group(1).strip()
    rest = line.text[m.end():].strip()
    if len(rest) > 5:
        return None
    if not _is_centered(line, body_w, tolerance_frac=0.25):
        return None
    return matched


def _flavor_start(line: Line) -> bool:
    return bool(line.text) and line.text.lstrip()[:1] in _OPEN_QUOTES


# Echtes Flavor endet auf Schluss-Quote; danach darf nur Whitespace stehen
# oder eine echte "— Author"-Zuschreibung (Em- oder En-Dash mit Leerraum).
# Ein einfacher Bindestrich (`-`) ohne Leerzeichen wäre `Wort-Suffix` mitten
# im Spielregeltext — kein Flavor.
_VALID_AFTER_QUOTE_RE = re.compile(r"^\s*(?:[—–]\s+[A-ZÄÖÜ].*)?$")


def _flavor_end(line: Line) -> bool:
    stripped = line.text.rstrip()
    if not stripped:
        return False
    # Suche nach der LETZTEN Schluss-Quote — Rest muss leer / Author-Attribution sein.
    last = max((stripped.rfind(q) for q in _CLOSE_QUOTES), default=-1)
    if last < 0:
        return False
    after = stripped[last + 1 :]
    return bool(_VALID_AFTER_QUOTE_RE.match(after))


def split_sections(lines: list[Line], body_w: int, type_code: str | None = None) -> dict:
    """Liefert {'traits': str, 'text': str, 'flavor': str}.
    Felder können '' sein, wenn auf der Karte nichts entsprechendes ist.

    `type_code` (z.B. 'main_scheme', 'side_scheme', 'villain', ...) steuert
    Type-spezifische Heuristiken — derzeit nur die Leading-Flavor-Erkennung,
    die nur bei Schemes greift, weil dort die Flavor-Prosa VOR dem ersten
    Spielregel-Lemma steht.
    """
    out = {"traits": "", "text": "", "flavor": ""}
    if not lines:
        return out

    remaining = list(lines)

    # 1) Traits am Anfang: in den ersten 3 Zeilen suchen, OCR-Müll-Zeilen
    # davor überspringen (z.B. „EST NN /“ als Illustrations-Bleed-In).
    trait_chunks: list[str] = []
    i = 0
    while i < min(3, len(remaining)) and len(trait_chunks) < 2:
        match = _trait_match(remaining[i], body_w)
        if match is not None:
            trait_chunks.append(match)
            del remaining[i]
            # i bleibt — durch das del rutscht das nächste Element in dieselbe Position.
        else:
            i += 1
    if trait_chunks:
        out["traits"] = postprocess.finalize_traits(" ".join(trait_chunks))

    # 1b) Leading-Flavor (nur bei Schemes): Prosa-Zeilen, die vor dem ersten
    # Spielregel-Lemma stehen, sind die Flavor-Beschreibung. Wir akzeptieren
    # sie nur, wenn nach dem Prosa-Block tatsächlich ein Lemma folgt — sonst
    # könnte es sich auch nur um misglückte OCR-Anfangszeilen handeln.
    if type_code in ("main_scheme", "side_scheme") and remaining:
        prose_idx: list[int] = []
        for j in range(min(5, len(remaining))):
            if _looks_like_lemma_start(remaining[j].text):
                break
            prose_idx.append(j)
        next_after = (prose_idx[-1] + 1) if prose_idx else 0
        if (
            prose_idx
            and next_after < len(remaining)
            and _looks_like_lemma_start(remaining[next_after].text)
        ):
            flavor_lines = [remaining[k] for k in prose_idx]
            for k in reversed(prose_idx):
                del remaining[k]
            out["flavor"] = postprocess.finalize_flavor(
                "\n".join(l.text for l in flavor_lines)
            )

    # 2) Trailing-Flavor am Ende: ein zusammenhängender Quote-Block, der
    # innerhalb der LETZTEN ~3 Zeilen anfängt — sonst war das nur ein Zitat
    # im Body. Wenn schon Leading-Flavor (Schemes) ermittelt wurde,
    # überspringen wir das, damit nicht beide gleichzeitig gesetzt werden.
    flavor_lines: list[Line] = []
    if remaining and not out["flavor"]:
        last_idx = len(remaining) - 1
        end_idx = None
        for i in range(last_idx, -1, -1):
            if _flavor_end(remaining[i]):
                end_idx = i
                break
        if end_idx is not None:
            start_idx = -1
            search_min = max(end_idx - 3, 0)  # Flavor max 4 Zeilen lang
            for i in range(end_idx, search_min - 1, -1):
                if _flavor_start(remaining[i]):
                    start_idx = i
                    break
            # Zusätzlich: Start muss in den letzten 4 non-empty Zeilen liegen,
            # damit „Zitat im Body" nicht fälschlich Flavor wird.
            if start_idx >= 0 and start_idx >= len(remaining) - 4:
                flavor_lines = remaining[start_idx : end_idx + 1]
                del remaining[start_idx : end_idx + 1]

    if flavor_lines and not out["flavor"]:
        out["flavor"] = postprocess.finalize_flavor(
            "\n".join(line.text for line in flavor_lines)
        )

    # 3) Text: was übrig bleibt.
    if remaining:
        out["text"] = postprocess.finalize_text(
            "\n".join(line.text for line in remaining)
        )

    return out
