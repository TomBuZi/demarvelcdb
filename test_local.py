"""
Lokaler Test ohne Discord. Aufruf:
    python test_local.py Tigra
    python test_local.py "Spider-Man"
    python test_local.py "[[Tigra]]"
    python test_local.py "Ich such [[Tigra]] und [[Nick Fury]]"
"""
import sys
import io
import re

# Windows-Terminals nutzen oft CP1252 – UTF-8 erzwingen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import urllib.request
import json
from card_search import search_cards

DE_API_URL    = "https://de.marvelcdb.com/api/public/cards/"
DE_PACKS_URL  = "https://de.marvelcdb.com/api/public/packs/"
GITHUB_RAW    = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master"
DE_TRANS_BASE = f"{GITHUB_RAW}/translations/de/pack"
EN_PACK_BASE  = f"{GITHUB_RAW}/pack"
DE_OVERLAY    = ("name", "text", "traits", "flavor", "subname")


def _fetch_json(url: str) -> list | dict | None:
    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def load_encounter_cards() -> list:
    packs_data = _fetch_json(DE_PACKS_URL) or []
    pack_map   = {p["code"]: p["name"] for p in packs_data}

    result = []
    for pack_code, pack_name in pack_map.items():
        en_cards = _fetch_json(f"{EN_PACK_BASE}/{pack_code}_encounter.json")
        if not en_cards:
            continue

        de_entries = _fetch_json(f"{DE_TRANS_BASE}/{pack_code}_encounter.json") or []
        de_map = {c["code"]: c for c in de_entries}

        for card in en_cards:
            card = dict(card)
            card.setdefault("pack_code",    pack_code)
            card.setdefault("pack_name",    pack_name)
            card.setdefault("faction_code", "encounter")
            card.setdefault("faction_name", "Encounter")
            card["real_name"]   = card.get("name", "")
            card["real_text"]   = card.get("text", "")
            card["real_traits"] = card.get("traits", "")
            if card["code"] in de_map:
                for field in DE_OVERLAY:
                    if field in de_map[card["code"]]:
                        card[field] = de_map[card["code"]][field]
            result.append(card)

    return result

ICON_MAP = {
    r"\[energy\]":     "⚡",
    r"\[physical\]":   "👊",
    r"\[mental\]":     "🧠",
    r"\[wild\]":       "🌟",
    r"\[hero\]":       "🦸",
    r"\[villain\]":    "💀",
    r"\[unique\]":     "★",
    r"\[star\]":       "★",
    r"\[boost\]":      "▲",
    r"\[attack\]":     "⚔️",
    r"\[thwart\]":     "🛡️",
    r"\[defense\]":    "🛡️",
    r"\[recover\]":    "❤️",
    r"\[per_hero\]":   "/Held",
    r"\[per_player\]": "/Spieler",
}

PAGE_SIZE = 20

TYPE_LABELS = {
    "hero":        "Held",
    "alter_ego":   "Alter Ego",
    "ally":        "Verbündeter",
    "event":       "Ereignis",
    "resource":    "Ressource",
    "support":     "Unterstützung",
    "upgrade":     "Verbesserung",
    "villain":     "Schurke",
    "main_scheme": "Hauptplan",
    "side_scheme": "Nebenplan",
    "minion":      "Scherge",
    "treachery":   "Verrat",
    "obligation":  "Verpflichtung",
    "environment": "Umgebung",
}


def html_to_text(text: str) -> str:
    text = re.sub(r"<b>(.*?)</b>", r"[\1]", text, flags=re.DOTALL)
    text = re.sub(r"<i>(.*?)</i>", r"_\1_", text, flags=re.DOTALL)
    text = re.sub(r"<em>(.*?)</em>", r"_\1_", text, flags=re.DOTALL)
    text = re.sub(r"<strong>(.*?)</strong>", r"[\1]", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n        ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[\[(.+?)]]", r"*\1*", text)
    return text


def fmt(text: str) -> str:
    if not text:
        return ""
    text = html_to_text(text)
    for pattern, replacement in ICON_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def print_card(card: dict):
    SEP = "─" * 52
    type_code = card.get("type_code", "")

    name = card.get("name") or card.get("real_name", "?")
    subname = card.get("subname")
    unique = "★ " if card.get("is_unique") else ""
    headline = f"{unique}{name}"
    if subname:
        headline += f" – {subname}"

    print(f"\n{SEP}")
    print(f"  {headline}")
    print(SEP)

    type_label = TYPE_LABELS.get(type_code, type_code)
    faction    = card.get("faction_name", "")
    pack       = card.get("pack_name", "")
    meta = type_label
    if faction and faction.lower() not in ("hero", "villain", "encounter", type_code):
        meta += f" · {faction}"
    if pack:
        meta += f"  [{pack}]"
    print(f"  Typ:  {meta}")

    traits = card.get("traits") or card.get("real_traits")
    if traits:
        print(f"  Merkm: {traits}")

    print()

    stats = []
    if type_code in ("hero", "alter_ego"):
        if card.get("health") is not None:
            star = "★" if card.get("health_star") else ""
            stats.append(f"LP {card['health']}{star}")
        if card.get("hand_size") is not None:
            stats.append(f"Hand {card['hand_size']}")
    if type_code == "hero":
        for lbl, key, sk in [("ANG", "attack",  "attack_star"),
                              ("WID", "thwart",  "thwart_star"),
                              ("VER", "defense", "defense_star")]:
            if card.get(key) is not None:
                star = "★" if card.get(sk) else ""
                stats.append(f"{lbl} {card[key]}{star}")
    if type_code == "alter_ego":
        if card.get("recover") is not None:
            star = "★" if card.get("recover_star") else ""
            stats.append(f"ERH {card['recover']}{star}")
    if type_code in ("ally", "minion", "villain"):
        if card.get("cost") is not None:
            stats.append(f"Kost {card['cost']}")
        for lbl, key, sk, cost_key in [
            ("LP",  "health", "health_star", None),
            ("ANG", "attack", "attack_star", "attack_cost"),
            ("WID", "thwart", "thwart_star", "thwart_cost"),
        ]:
            if card.get(key) is not None:
                star = "★" if card.get(sk) else ""
                act = "🎯" * (card.get(cost_key) or 0) if cost_key else ""
                stats.append(f"{lbl} {card[key]}{star}{' ' + act if act else ''}")
    if type_code in ("event", "support", "upgrade", "resource", "obligation"):
        if card.get("cost") is not None:
            stats.append(f"Kost {card['cost']}")
    if type_code in ("main_scheme", "side_scheme"):
        if card.get("base_threat") is not None:
            per = "/Held" if card.get("base_threat_per_group") else ""
            stats.append(f"Bedrohung {card['base_threat']}{per}")

    res_icons = []
    for res, icon in [("resource_energy", "⚡"), ("resource_physical", "👊"),
                      ("resource_mental", "🧠"), ("resource_wild", "🌟")]:
        val = card.get(res)
        if val:
            res_icons.append(icon * val)
    if res_icons:
        stats.append("Res " + " ".join(res_icons))

    if stats:
        print("  " + "  |  ".join(stats))
        print()

    text = fmt(card.get("text") or "")
    if text:
        print(f"  Kartentext:")
        for line in text.splitlines():
            print(f"        {line}")
        print()

    flavor = card.get("flavor")
    if flavor:
        print(f"  _{flavor}_")
        print()

    url = card.get("url", "")
    if url:
        print(f"  {url}")
    print(SEP)


def card_menu_line(i: int, card: dict) -> str:
    """Numbered list entry for the selection menu."""
    type_label  = TYPE_LABELS.get(card.get("type_code", ""), card.get("type_code", ""))
    faction     = card.get("faction_name", "")
    name        = card.get("name") or card.get("real_name", "?")
    subname     = card.get("subname")
    unique      = "★ " if card.get("is_unique") else ""

    label = f"{unique}{name}"
    if subname:
        label += f" – {subname}"

    desc_parts = [type_label]
    if faction and faction.lower() not in ("hero", "villain", "encounter",
                                           card.get("type_code", "")):
        desc_parts.append(faction)
    desc = " · ".join(desc_parts)

    return f"  [{i:2}]  {label:<35}  {desc}"


def pick_card(matches: list) -> dict | None:
    total   = len(matches)
    offset  = 0

    while True:
        page  = matches[offset:offset + PAGE_SIZE]
        start = offset + 1
        end   = offset + len(page)

        print(f"\n{total} Treffer – Ergebnisse {start}–{end} von {total}:\n")
        for i, c in enumerate(page):
            print(card_menu_line(offset + i + 1, c))
        print()

        nav = []
        if offset > 0:
            nav.append("v = vorherige Seite")
        if offset + PAGE_SIZE < total:
            nav.append("n = nächste Seite")
        nav.append("Enter = Abbrechen")

        prompt = f"Nummer (1–{total}), {', '.join(nav)}: "
        raw = input(prompt).strip().lower()

        if not raw:
            return None
        if raw == "n" and offset + PAGE_SIZE < total:
            offset += PAGE_SIZE
        elif raw == "v" and offset > 0:
            offset -= PAGE_SIZE
        elif raw.isdigit() and 1 <= int(raw) <= total:
            return matches[int(raw) - 1]
        else:
            print("Ungültige Eingabe.")


def main():
    raw_input = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not raw_input:
        raw_input = input("Nachricht oder Kartenname: ").strip()

    # [[...]] Syntax unterstützen, sonst als direkter Suchbegriff behandeln
    queries = re.findall(r'\[\[(.+?)]]', raw_input) or [raw_input]

    print("Lade Spielerkarten von MarvelCDB (de) …")
    with urllib.request.urlopen(DE_API_URL) as resp:
        cards = json.loads(resp.read().decode("utf-8"))
    print(f"{len(cards)} Spielerkarten geladen.")

    # Encounter-Karten deaktiviert (zu langsam beim Start)
    # print("Lade Encounter-Karten von GitHub …")
    # encounter_cards = load_encounter_cards()
    # print(f"{len(encounter_cards)} Encounter-Karten geladen.")
    # cards = cards + encounter_cards

    for query in queries:
        query = query.strip()
        if len(query) < 3:
            print(f'"{query}": Bitte mindestens 3 Buchstaben angeben.')
            continue

        matches = search_cards(cards, query)

        if not matches:
            print(f'\nKeine Karte gefunden für „{query}".')
            continue

        if len(matches) == 1:
            print_card(matches[0])
            continue

        card = pick_card(matches)
        if card is None:
            print("Abgebrochen.")
            continue

        print_card(card)


if __name__ == "__main__":
    main()
