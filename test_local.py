"""
Lokaler Test ohne Discord. Aufruf:
    python test_local.py Tigra
    python test_local.py "Spider-Man"
"""
import sys
import io
import re

# Windows-Terminals nutzen oft CP1252 – UTF-8 erzwingen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
import urllib.request
import json

DE_API_URL = "https://de.marvelcdb.com/api/public/cards/"

ICON_MAP = {
    r"\[energy\]":     "⚡",
    r"\[physical\]":   "👊",
    r"\[mental\]":     "🧠",
    r"\[wild\]":       "🌟",
    r"\[hero\]":       "🦸",
    r"\[villain\]":    "💀",
    r"\[unique\]":     "★",
    r"\[boost\]":      "▲",
    r"\[attack\]":     "⚔️",
    r"\[thwart\]":     "🛡️",
    r"\[defense\]":    "🛡️",
    r"\[recover\]":    "❤️",
    r"\[per_hero\]":   "/Held",
    r"\[per_player\]": "/Spieler",
}

MAX_SELECT = 25  # wie im Discord-Bot

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
        for lbl, key, sk in [("ATK", "attack", "attack_star"),
                              ("THW", "thwart", "thwart_star"),
                              ("DEF", "defense", "defense_star")]:
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
        for lbl, key, sk in [("LP", "health", "health_star"),
                              ("ATK", "attack", "attack_star"),
                              ("THW", "thwart", "thwart_star")]:
            if card.get(key) is not None:
                star = "★" if card.get(sk) else ""
                stats.append(f"{lbl} {card[key]}{star}")
        if card.get("attack_cost") is not None:
            stats.append(f"ATK-AKT {card['attack_cost']}")
        if card.get("thwart_cost") is not None:
            stats.append(f"THW-AKT {card['thwart_cost']}")
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
    """Interactive selection when multiple cards match."""
    if len(matches) > MAX_SELECT:
        print(f"\n{len(matches)} Treffer – bitte den Namen genauer angeben.")
        return None

    print(f"\n{len(matches)} Treffer – bitte eine Karte wählen:\n")
    for i, c in enumerate(matches, 1):
        print(card_menu_line(i, c))
    print()

    while True:
        raw = input(f"Nummer (1–{len(matches)}) oder Enter zum Abbrechen: ").strip()
        if not raw:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(matches):
            return matches[int(raw) - 1]
        print("Ungültige Eingabe.")


def main():
    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not query:
        query = input("Kartenname suchen: ").strip()
    if not query:
        print("Kein Suchbegriff angegeben.")
        sys.exit(1)

    print("Lade Karten von MarvelCDB (de) …")
    with urllib.request.urlopen(DE_API_URL) as resp:
        cards = json.loads(resp.read().decode("utf-8"))
    print(f"{len(cards)} Karten geladen.")

    q = query.lower()
    matches = [
        c for c in cards
        if (q in (c.get("name") or "").lower()
        or q in (c.get("real_name") or "").lower())
        and not c.get("duplicate_of")
    ]

    if not matches:
        print(f'\nKeine Karte gefunden, die „{query}" enthält.')
        sys.exit(0)

    if len(matches) == 1:
        print_card(matches[0])
        return

    card = pick_card(matches)
    if card is None:
        print("Abgebrochen.")
        sys.exit(0)

    print_card(card)


if __name__ == "__main__":
    main()
