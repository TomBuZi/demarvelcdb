"""Exportiert alle The Hood-Karten als hübsch formatierte Textdatei.

Nutzt denselben Formatter wie der Discord-Bot (card_formatter.build_embed) und
schreibt Titel + Description jeder Karte in eine Textdatei. So sieht der Output
genauso aus wie im Bot — nur als Klartext mit Markdown-Auszeichnungen.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from card_formatter import build_embed, TYPE_LABELS  # noqa: E402

DE_PATH = ROOT / "translations_local" / "hood_encounter.json"
EN_CACHE = ROOT / "tools" / ".hood_encounter_en.json"
EN_URL = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master/pack/hood_encounter.json"
DE_TRANS_URL = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master/translations/de/pack/hood_encounter.json"
DE_TRANS_CACHE = ROOT / "tools" / ".hood_encounter_de_github.json"
SETS_EN_URL = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master/sets.json"
SETS_EN_CACHE = ROOT / "tools" / ".sets_en.json"
SETS_DE_URL = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master/translations/de/sets.json"
SETS_DE_CACHE = ROOT / "tools" / ".sets_de.json"
DST = ROOT / "hood_cards_de.txt"

WIDTH = 78
DE_OVERLAY_FIELDS = ("name", "text", "traits", "flavor", "subname")


def fetch_cached(url: str, cache: Path, optional: bool = False) -> list[dict]:
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    print(f"Lade {url} ...")
    try:
        with urllib.request.urlopen(url) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if optional and e.code == 404:
            cache.write_text("[]", encoding="utf-8")
            return []
        raise
    cache.write_text(raw, encoding="utf-8")
    return json.loads(raw)


def merge(en: list[dict]) -> list[dict]:
    """Englische Pack-Daten + GitHub-DE + lokales Overlay (lokales Overlay gewinnt)."""
    de_github = fetch_cached(DE_TRANS_URL, DE_TRANS_CACHE, optional=True)
    de_local = json.loads(DE_PATH.read_text(encoding="utf-8"))

    de_map: dict[str, dict] = {}
    for entry in de_github:
        de_map[entry["code"]] = dict(entry)
    for entry in de_local:
        code = entry.get("code")
        if not code:
            continue
        de_map.setdefault(code, {}).update(
            {k: v for k, v in entry.items() if k in DE_OVERLAY_FIELDS}
        )

    merged = []
    for card in en:
        c = dict(card)
        c.setdefault("pack_code", "hood")
        c.setdefault("pack_name", "The Hood")
        c.setdefault("faction_code", "encounter")
        c.setdefault("faction_name", "Encounter")
        for f in DE_OVERLAY_FIELDS:
            c[f"real_{f}"] = c.get(f, "")
        if c["code"] in de_map:
            for f in DE_OVERLAY_FIELDS:
                if f in de_map[c["code"]]:
                    c[f] = de_map[c["code"]][f]
        merged.append(c)
    return merged


def wrap_line(line: str, width: int) -> list[str]:
    if not line:
        return [""]
    out = []
    while len(line) > width:
        cut = line.rfind(" ", 0, width)
        if cut <= 0:
            cut = width
        out.append(line[:cut].rstrip())
        line = line[cut:].lstrip()
    out.append(line)
    return out


def wrap_text(text: str, width: int) -> str:
    return "\n".join(w for raw in text.split("\n") for w in wrap_line(raw, width))


def set_label(card: dict, sets_map: dict[str, str]) -> str | None:
    code = card.get("set_code")
    if not code:
        return None
    name = sets_map.get(code, code.replace("_", " ").title())
    pos = card.get("set_position")
    if pos:
        return f"Begegnungsset: *{name}* (#{pos})"
    return f"Begegnungsset: *{name}*"


def render_card(card: dict, sets_map: dict[str, str]) -> str:
    embed = build_embed(card, custom_emojis=None, lang="de")
    title = embed.title or ""
    desc = embed.description or ""

    # Set-Zeile direkt nach der Typ-Zeile einfügen (= 1. Zeile der Description).
    set_line = set_label(card, sets_map)
    if set_line:
        parts = desc.split("\n", 1)
        if len(parts) == 2:
            desc = f"{parts[0]}  ·  {set_line}\n{parts[1]}"
        else:
            desc = f"{parts[0]}  ·  {set_line}"

    desc = wrap_text(desc, WIDTH)

    sep = "─" * WIDTH
    return "\n".join([sep, title, sep, desc, ""])


def load_sets_map() -> dict[str, str]:
    """code -> Anzeigename (DE bevorzugt, sonst EN-Fallback)."""
    en_sets = fetch_cached(SETS_EN_URL, SETS_EN_CACHE)
    de_sets = fetch_cached(SETS_DE_URL, SETS_DE_CACHE, optional=True)
    name_map = {s["code"]: s["name"] for s in en_sets}
    for s in de_sets:
        if s.get("name"):
            name_map[s["code"]] = s["name"]
    return name_map


def main() -> None:
    en_cards = fetch_cached(EN_URL, EN_CACHE)
    sets_map = load_sets_map()
    merged = merge(en_cards)

    merged.sort(key=lambda c: (c.get("position") or 0, c.get("code", "")))

    parts = []
    parts.append("═" * WIDTH)
    parts.append("THE HOOD — Vollständige Kartenliste (Deutsch)".center(WIDTH))
    parts.append(f"{len(merged)} Karten".center(WIDTH))
    parts.append("═" * WIDTH)
    parts.append("")

    # Inhaltsverzeichnis nach Typ
    by_type: dict[str, list[dict]] = {}
    for c in merged:
        by_type.setdefault(c.get("type_code", ""), []).append(c)
    parts.append("Übersicht:")
    for tc, cards in by_type.items():
        label = TYPE_LABELS.get(tc, tc or "?")
        parts.append(f"  • {label}: {len(cards)}")
    parts.append("")

    for card in merged:
        parts.append(render_card(card, sets_map))

    DST.write_text("\n".join(parts), encoding="utf-8")
    print(f"Geschrieben: {DST}  ({len(merged)} Karten)")


if __name__ == "__main__":
    main()
