"""
Converts MarvelCDB card dicts (German locale) into Discord embeds.
"""
import re
import discord

_ICON_DEFAULTS = {
    "energy":       "⚡",
    "physical":     "👊",
    "mental":       "🧠",
    "wild":         "🌟",
    "hero":         "🦸",
    "villain":      "💀",
    "unique":       "★",
    "star":         "★",
    "boost":        "▲",
    "attack":       "⚔️",
    "thwart":       "🛡️",
    "defense":      "🛡️",
    "recover":      "❤️‍🩹",
    "per_hero":     "/Held",
    "per_player":   "/Spieler",
    "acceleration": "",
    "amplify":      "",
    "crisis":       "",
    "hazard":       "",
    "consequential_damage": "",
    "infinite":     "",
}

def _build_icon_map(custom: dict) -> dict:
    result = {}
    for key, default in _ICON_DEFAULTS.items():
        result[key] = custom.get(f"cardicon_{key}") or default
    result["per_hero"] = custom.get("cardicon_per_player") or result["per_hero"]
    return result

FACTION_COLORS = {
    "aggression": 0xE03030,
    "justice":    0xF0C040,
    "leadership": 0x3060D0,
    "protection": 0x30A050,
    "hero":       0xA020A0,
    "villain":    0x202020,
    "encounter":  0x804010,
}

from card_search import search_cards  # noqa: F401 – re-exported for convenience

TYPE_LABELS = {
    "hero":        "Held",
    "alter_ego":   "Alter Ego",
    "ally":        "Verbündeter",
    "event":       "Ereignis",
    "resource":    "Ressource",
    "support":     "Unterstützung",
    "upgrade":     "Upgrade",
    "villain":     "Schurke",
    "main_scheme": "Hauptplan",
    "side_scheme": "Nebenplan",
    "minion":      "Scherge",
    "treachery":   "Verrat",
    "obligation":  "Verpflichtung",
    "environment": "Umgebung",
}

IMAGE_BASE = "https://marvelcdb.com"


def _html_to_discord(text: str) -> str:
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<i>(.*?)</i>", r"*\1*", text, flags=re.DOTALL)
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.DOTALL)
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[\[(.+?)]]", r"***\1***", text)
    return text


def _fmt(text: str, icons: dict) -> str:
    if not text:
        return ""
    text = _html_to_discord(text)
    for key, symbol in icons.items():
        text = re.sub(r"\[" + key + r"\]", symbol, text, flags=re.IGNORECASE)
    return text


def _stat(label: str, value, star: bool = False, star_icon: str = "★"):
    if value is None:
        return None
    return f"**{label}:** {value}{star_icon if star else ''}"


def build_embed(card: dict, custom_emojis: dict | None = None) -> discord.Embed:
    icons     = _build_icon_map(custom_emojis or {})
    type_code = card.get("type_code", "")
    faction   = card.get("faction_code", "")
    color     = FACTION_COLORS.get(faction, FACTION_COLORS.get(type_code, 0x888888))
    if card.get("has_errata"):
        color = 0xCC0000

    # Title
    title = card.get("name") or card.get("real_name", "Unbekannt")
    if card.get("stage"):
        title = f"{title} ({card['stage']})"
    subname = card.get("subname")
    if subname:
        title = f"{title} – {subname}"
    if card.get("is_unique"):
        title = f"{icons['unique']} {title}"

    url = card.get("url") or ""
    embed = discord.Embed(title=title, color=color, url=url)

    imagesrc = card.get("imagesrc")
    if imagesrc:
        embed.set_thumbnail(url=IMAGE_BASE + imagesrc)

    type_label   = TYPE_LABELS.get(type_code, type_code)
    faction_name = card.get("faction_name", "")
    all_packs    = card.get("all_packs") or [{"pack_name": card.get("pack_name", ""), "position": card.get("position"), "quantity": card.get("quantity")}]
    traits       = card["traits"] if "traits" in card else card.get("real_traits")
    show_faction = faction_name and faction_name.lower() not in (type_code, "hero", "villain", "encounter")
    desc = f"{faction_name}\n**{type_label}**" if show_faction else f"**{type_label}**"

    # Werte
    stats = []

    if type_code in ("hero", "alter_ego"):
        per = icons["per_hero"] if card.get("health_per_hero") else ""
        s = _stat("LP", card.get("health"), card.get("health_star", False), icons["star"])
        if s: stats.append(s + per)
        s = _stat("Handkarten", card.get("hand_size"))
        if s: stats.append(s)

    if type_code == "hero":
        for label, key, sk in [
            ("WID", "thwart",  "thwart_star"),
            ("ANG", "attack",  "attack_star"),
            ("VER", "defense", "defense_star"),
            ("ERH", "recover", "recover_star"),
        ]:
            s = _stat(label, card.get(key), card.get(sk, False), icons["star"])
            if s: stats.append(s)

    if type_code == "alter_ego":
        s = _stat("ERH", card.get("recover"), card.get("recover_star", False), icons["star"])
        if s: stats.append(s)

    if type_code in ("ally", "minion", "villain"):
        cost = card.get("cost")
        if cost is not None:
            per = icons["per_hero"] if card.get("cost_per_hero") else ""
            stats.append(f"**Kosten:** {cost}{per}")
        for label, key, sk, cost_key in [
            ("WID", "thwart",  "thwart_star",  "thwart_cost"),
            ("PLA", "scheme",  "scheme_star",  None),
            ("ANG", "attack",  "attack_star",  "attack_cost"),
            ("VER", "defense", "defense_star", None),
            ("ERH", "recover", "recover_star", None),
            ("LP",  "health",  "health_star",  None),
        ]:
            val = card.get(key)
            if val is None:
                continue
            star = icons["star"] if card.get(sk) else ""
            cd = icons.get("consequential_damage", "💥")
            act = cd * (card.get(cost_key) or 0) if cost_key else ""
            per = icons["per_hero"] if key == "health" and card.get("health_per_hero") else ""
            stats.append(f"**{label}:** {val}{star}{per}{' ' + act if act else ''}")

    if type_code in ("event", "support", "upgrade", "resource", "obligation"):
        cost = card.get("cost")
        if cost is not None:
            per = icons["per_hero"] if card.get("cost_per_hero") else ""
            stats.append(f"**Kosten:** {cost}{per}")

    if type_code in ("main_scheme", "side_scheme"):
        bt = card.get("base_threat")
        if bt is not None:
            per = " pro Held" if card.get("base_threat_per_group") else ""
            stats.append(f"**Startbedrohung:** {bt}{per}")
        et = card.get("escalation_threat")
        if et is not None:
            per = " pro Held" if card.get("escalation_threat_per_group") else ""
            stats.append(f"**Eskalation:** {et}{per}")

    if stats:
        desc += "\n" + "\n".join(stats)

    # Traits · Kartentext · Flavor · Ressourcen · Pack
    text = _fmt(card.get("text") or "", icons)
    flavor = card.get("flavor")

    if traits:
        desc += f"\n***{traits}***"
    if text:
        desc += f"\n\n{text}"
    if flavor:
        desc += f"\n*{flavor}*"

    scheme_icons = []
    for field, key in [
        ("scheme_hazard", "hazard"), ("scheme_crisis", "crisis"),
        ("scheme_acceleration", "acceleration"), ("scheme_amplify", "amplify"),
    ]:
        val = card.get(field)
        if val:
            scheme_icons.append(icons[key] * val)
    if scheme_icons:
        desc += f"\n{'  '.join(scheme_icons)}"

    resources = []
    for res, key in [
        ("resource_energy", "energy"), ("resource_physical", "physical"),
        ("resource_mental", "mental"), ("resource_wild", "wild"),
    ]:
        val = card.get(res)
        if val:
            resources.append(icons[key] * val)
    if resources:
        desc += f"\n**Ressourcen:** {'  '.join(resources)}"

    pack_lines = []
    for p in all_packs:
        if not p.get("pack_name"):
            continue
        line = p["pack_name"]
        if p.get("position"):
            line += f" #{p['position']}"
        if p.get("quantity"):
            line += f" ({p['quantity']})"
        pack_lines.append(line)
    if card.get("has_errata"):
        desc += "\n\n***ERRATA***"
    if pack_lines:
        desc += "\n\n*" + "\n".join(pack_lines) + "*"

    embed.description = desc
    return embed
