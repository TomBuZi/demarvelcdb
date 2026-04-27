"""Postprocessing für rohe OCR-Ergebnisse einer einzelnen Karte.

Tesseract liefert Plain-Text. Das zzorba-Schema verlangt:
- `<b>...</b>` für Stichwort-Lemmata wie 'Sobald aufgedeckt:'
- `<i>...</i>` für Flavor-Texte und einige Spezial-Effekt-Lemmata
- `[energy]`, `[mental]`, `[physical]` für die entsprechenden Spielsymbole

Diese Heuristiken decken die häufigsten Fälle automatisch ab. Was sie nicht
treffen, wird beim manuellen Review nachgepflegt.
"""

from __future__ import annotations

import re

# Lemmata, die typischerweise in <b> stehen, am Zeilenanfang gefolgt von Doppelpunkt.
# Reihenfolge: längere Patterns zuerst, damit kurze Patterns nicht falsch greifen.
BOLD_LEMMATA = [
    r"Sobald aufgedeckt",
    r"Wenn besiegt",
    r"Wenn aufgenommen",
    r"Sobald in Spiel",
    r"Erzwungene Reaktion",
    r"Erzwungene Unterbrechung",
    r"Reaktion",
    r"Unterbrechung",
    r"Held[- ]Aktion",
    r"Alter[- ]?Ego[- ]Aktion",
    r"Aktion",
    r"Krise",
    r"Gefahr",
    r"Beschleunigung",
    r"Spezial",
    r"Boost",
    r"Wache",
    r"Steady",
    r"Stählern",
    r"Vergeltung",
]

# Roh-OCR-Token, die für Spielsymbole stehen können. Werden auf [energy]/[mental]/
# [physical] gemappt. Tabelle wächst während des Reviews — neue Treffer hier
# eintragen, dann erneut --consolidate laufen lassen.
SYMBOL_REPLACEMENTS = {
    # Energy (gelber Blitz)
    "[E]": "[energy]",
    "(E)": "[energy]",
    "[Energie]": "[energy]",
    "(Energie)": "[energy]",
    # Mental (blauer Bolzen)
    "[M]": "[mental]",
    "(M)": "[mental]",
    "[Mental]": "[mental]",
    # Physical (rote Faust)
    "[P]": "[physical]",
    "(P)": "[physical]",
    "[Physisch]": "[physical]",
    # Held-/Schurken-Symbole
    "[Held]": "[hero]",
    "(Held)": "[hero]",
    "[Schurke]": "[villain]",
}


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    # Zeilen normalisieren, Hyphen-Trennungen am Zeilenende zusammenziehen
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"-\n(\w)", r"\1", text)  # "Begeg-\nnungs" -> "Begegnungs"
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def apply_symbol_table(text: str) -> str:
    if not text:
        return ""
    for raw, replacement in SYMBOL_REPLACEMENTS.items():
        text = text.replace(raw, replacement)
    return text


def apply_bold_lemmata(text: str) -> str:
    """Setzt <b>...</b> um Lemmata, die jeweils am Zeilenanfang oder direkt
    nach einem Bullet '*'/'•' stehen und mit ':' enden.
    """
    if not text:
        return ""
    pattern = r"(^|\n|[*•]\s*)(" + "|".join(BOLD_LEMMATA) + r")(:)"
    return re.sub(pattern, lambda m: f"{m.group(1)}<b>{m.group(2)}</b>{m.group(3)}", text)


def normalize_quotes(text: str) -> str:
    """Wandelt typografische und glyphfehlerhafte Anführungszeichen in das
    deutsche Schema „..." um, das in vorhandenen Übersetzungen verwendet wird.
    """
    if not text:
        return ""
    # OCR liefert manchmal " ", "''" oder ähnlich verbogenes Material — wir
    # vereinheitlichen auf typografische deutsche Anführungszeichen.
    text = re.sub(r"^[\"'`´]+", "„", text)
    text = re.sub(r"[\"'`´]+$", "“", text)
    return text


def finalize_text(raw_text: str) -> str:
    """Volle Pipeline für den Hauptkartentext."""
    out = normalize_whitespace(raw_text)
    out = apply_symbol_table(out)
    out = apply_bold_lemmata(out)
    return out


def finalize_traits(raw_text: str) -> str:
    out = normalize_whitespace(raw_text)
    # OCR liest den Trait-Punkt häufig als Komma — vor der weiteren
    # Normalisierung auf Punkt zurückbiegen ("TECH. WAFFE," → "TECH. WAFFE.").
    out = re.sub(r",(\s|$)", r".\1", out)
    # Traits sind eine Punkte-getrennte Liste, ein Punkt am Ende ist Standard.
    out = re.sub(r"\s*\.\s*", ". ", out).strip()
    if out and not out.endswith("."):
        out += "."
    return out


def finalize_name(raw_text: str) -> str:
    out = normalize_whitespace(raw_text)
    # Mehrfache Leerzeichen + Sonderzeichen weg — Kartennamen sind kurz und
    # enthalten praktisch keine Steuerzeichen.
    out = re.sub(r"[ ]+", " ", out)
    return out.strip()


def finalize_flavor(raw_text: str) -> str:
    out = normalize_whitespace(raw_text)
    out = normalize_quotes(out)
    if not out:
        return ""
    # Flavor ist standardmäßig kursiv. Falls schon Tags drin sind, nicht doppelt
    # einrahmen.
    if not out.startswith("<i>"):
        out = f"<i>{out}</i>"
    return out
