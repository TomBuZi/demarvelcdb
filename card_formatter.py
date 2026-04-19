"""
Converts MarvelCDB card dicts (German locale) into Discord embeds.
"""
import re
import discord

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
    r"\[recover\]":    "❤️‍🩹",
    r"\[per_hero\]":   "/Held",
    r"\[per_player\]": "/Spieler",
}

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
    "upgrade":     "Verbesserung",
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


def _fmt(text: str) -> str:
    if not text:
        return ""
    text = _html_to_discord(text)
    for pattern, replacement in ICON_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _stat(label: str, value, star: bool = False):
    if value is None:
        return None
    return f"**{label}:** {value}{'★' if star else ''}"


def build_embed(card: dict) -> discord.Embed:
    type_code = card.get("type_code", "")
    faction   = card.get("faction_code", "")
    color     = FACTION_COLORS.get(faction, FACTION_COLORS.get(type_code, 0x888888))

    # Title
    title = card.get("name") or card.get("real_name", "Unbekannt")
    subname = card.get("subname")
    if subname:
        title = f"{title} – {subname}"
    if card.get("is_unique"):
        title = f"★ {title}"

    url = card.get("url") or ""
    embed = discord.Embed(title=title, color=color, url=url)

    imagesrc = card.get("imagesrc")
    if imagesrc:
        embed.set_thumbnail(url=IMAGE_BASE + imagesrc)

    # Type / Faction / Pack
    type_label   = TYPE_LABELS.get(type_code, type_code)
    faction_name = card.get("faction_name", "")
    pack_name    = card.get("pack_name", "")
    meta_parts   = [type_label]
    if faction_name and faction_name.lower() not in (type_code, "hero", "villain", "encounter"):
        meta_parts.append(faction_name)
    if pack_name:
        meta_parts.append(f"*{pack_name}*")
    embed.add_field(name="Typ / Set", value=" · ".join(meta_parts), inline=False)

    # Traits
    traits = card.get("traits") or card.get("real_traits")
    if traits:
        embed.add_field(name="Merkmale", value=traits, inline=False)

    # Stats
    stats = []

    if type_code in ("hero", "alter_ego"):
        s = _stat("LP", card.get("health"), card.get("health_star", False))
        if s:
            stats.append(s)
        s = _stat("Handkarten", card.get("hand_size"))
        if s:
            stats.append(s)

    if type_code == "hero":
        for label, key, sk in [
            ("Angriff",     "attack",   "attack_star"),
            ("Vereitlung",  "thwart",   "thwart_star"),
            ("Verteidigung","defense",  "defense_star"),
        ]:
            s = _stat(label, card.get(key), card.get(sk, False))
            if s:
                stats.append(s)

    if type_code == "alter_ego":
        s = _stat("Erholung", card.get("recover"), card.get("recover_star", False))
        if s:
            stats.append(s)

    if type_code in ("ally", "minion", "villain"):
        cost = card.get("cost")
        if cost is not None:
            stats.append(f"**Kosten:** {cost}")
        for label, key, sk in [
            ("LP",         "health",  "health_star"),
            ("Angriff",    "attack",  "attack_star"),
            ("Vereitlung", "thwart",  "thwart_star"),
        ]:
            s = _stat(label, card.get(key), card.get(sk, False))
            if s:
                stats.append(s)
        if card.get("attack_cost") is not None:
            stats.append(f"**Angriffs-AKT:** {card['attack_cost']}")
        if card.get("thwart_cost") is not None:
            stats.append(f"**Vereitlungs-AKT:** {card['thwart_cost']}")

    if type_code in ("event", "support", "upgrade", "resource", "obligation"):
        cost = card.get("cost")
        if cost is not None:
            stats.append(f"**Kosten:** {cost}")

    if type_code in ("main_scheme", "side_scheme"):
        bt = card.get("base_threat")
        if bt is not None:
            per = " pro Held" if card.get("base_threat_per_group") else ""
            stats.append(f"**Startbedrohung:** {bt}{per}")
        et = card.get("escalation_threat")
        if et is not None:
            per = " pro Held" if card.get("escalation_threat_per_group") else ""
            stats.append(f"**Eskalation:** {et}{per}")

    resources = []
    for res, icon in [
        ("resource_energy", "⚡"), ("resource_physical", "👊"),
        ("resource_mental", "🧠"), ("resource_wild", "🌟"),
    ]:
        val = card.get(res)
        if val:
            resources.append(icon * val)
    if resources:
        stats.append(f"**Ressourcen:** {'  '.join(resources)}")

    if stats:
        embed.add_field(name="Werte", value="\n".join(stats), inline=True)

    # Card text (German)
    text = _fmt(card.get("text") or "")
    if text:
        embed.add_field(name="Kartentext", value=text, inline=False)

    # Flavor
    flavor = card.get("flavor")
    if flavor:
        embed.add_field(name="\u200b", value=f"*{flavor}*", inline=False)

    return embed
