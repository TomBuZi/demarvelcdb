"""
Lädt eine veröffentlichte Deckliste von marvelcdb und baut daraus
Discord-Embeds: eine kompakte Übersicht (Held, Aspekt, Gesamtzahl)
und – auf Wunsch ephemer aufklappbar – die volle Karten-Liste,
gruppiert nach Typ, alphabetisch mit Anzahl und Aspekt-Emoji.
"""
import json
import discord
import aiohttp

from card_formatter import FACTION_COLORS, TYPE_LABELS

DECK_API_URL = "https://de.marvelcdb.com/api/public/deck/{deck_id}"
DECK_VIEW_URL = "https://de.marvelcdb.com/deck/view/{deck_id}"
CARD_VIEW_URL = "https://de.marvelcdb.com/card/{code}"

_TYPE_ORDER = ("hero", "alter_ego", "ally", "event", "support", "upgrade", "resource")

_ASPECT_LABELS_DE = {
    "aggression": "Aggression",
    "justice":    "Gerechtigkeit",
    "leadership": "Führung",
    "protection": "Schutz",
    "basic":      "Basis",
}

_ASPECT_FALLBACK = {
    "aggression": "(Aggr)",
    "justice":    "(Ger)",
    "leadership": "(Führ)",
    "protection": "(Schutz)",
    "basic":      "(Basis)",
}

_FORMAT_LABELS_DE = {
    "standard": "Standard",
    "current":  "Aktuell",
    "modular":  "Modular",
}

_FIELD_VALUE_LIMIT = 1024


async def fetch_deck(session: aiohttp.ClientSession, deck_id: str) -> dict | None:
    url = DECK_API_URL.format(deck_id=deck_id)
    try:
        async with session.get(url) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            return await resp.json(content_type=None)
    except Exception:
        return None


def _aspect_marker(faction_code: str | None, custom_emojis: dict) -> str:
    if not faction_code or faction_code == "hero":
        return ""
    for key in (f"aspect_{faction_code}", faction_code, f"cardicon_{faction_code}"):
        emoji = custom_emojis.get(key)
        if emoji:
            return emoji
    return _ASPECT_FALLBACK.get(faction_code, "")


def _parse_meta(deck: dict) -> dict:
    raw = deck.get("meta") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _truncate_field(lines: list[str]) -> str:
    out: list[str] = []
    used = 0
    for line in lines:
        addition = len(line) + (1 if out else 0)
        if used + addition > _FIELD_VALUE_LIMIT:
            out.append("… (gekürzt)")
            break
        out.append(line)
        used += addition
    return "\n".join(out)


def _aspect_color(deck: dict) -> int:
    aspect = _parse_meta(deck).get("aspect")
    return FACTION_COLORS.get(aspect) or FACTION_COLORS["hero"]


def _total_cards(deck: dict) -> int:
    return sum((deck.get("slots") or {}).values())


def build_deck_summary_embed(deck: dict, custom_emojis: dict) -> discord.Embed:
    """Kompakte Übersicht für die Hauptnachricht – ohne Kartenliste."""
    meta = _parse_meta(deck)
    aspect = meta.get("aspect")
    fmt = meta.get("format")

    deck_id = deck.get("id")
    deck_name = deck.get("name") or "Unbenanntes Deck"
    hero_name = deck.get("hero_name") or "Unbekannter Held"

    desc_parts = [f"**Held:** {hero_name}"]
    if aspect:
        marker = _aspect_marker(aspect, custom_emojis)
        aspect_label = _ASPECT_LABELS_DE.get(aspect, aspect.capitalize())
        desc_parts.append(f"**Aspekt:** {marker} {aspect_label}".strip())
    if fmt:
        desc_parts.append(f"**Format:** {_FORMAT_LABELS_DE.get(fmt, fmt.capitalize())}")
    desc_parts.append(f"**Karten:** {_total_cards(deck)}")
    if deck_id is not None:
        desc_parts.append(f"[Auf marvelcdb öffnen]({DECK_VIEW_URL.format(deck_id=deck_id)})")

    return discord.Embed(
        title=deck_name,
        description="\n".join(desc_parts),
        color=_aspect_color(deck),
    )


def build_deck_list_embed(deck: dict, cards_by_code: dict, custom_emojis: dict) -> discord.Embed:
    """Volle Kartenliste, gruppiert nach Typ – für die ephemere Antwort."""
    deck_id = deck.get("id")
    hero_name = deck.get("hero_name") or "Unbekannter Held"

    embed = discord.Embed(
        title=f"{hero_name} – Kartenliste",
        color=_aspect_color(deck),
    )

    slots: dict = deck.get("slots") or {}
    groups: dict[str, list[tuple[str, int, str, str]]] = {}
    unknown: list[tuple[str, int]] = []

    for code, qty in slots.items():
        card = cards_by_code.get(code)
        if not card:
            unknown.append((code, qty))
            continue
        type_code = card.get("type_code") or "other"
        name = card.get("name") or code
        faction = card.get("faction_code")
        url = card.get("url") or CARD_VIEW_URL.format(code=code)
        groups.setdefault(type_code, []).append((name, qty, faction, url))

    ordered_types = list(_TYPE_ORDER) + sorted(t for t in groups if t not in _TYPE_ORDER)
    total = 0
    for type_code in ordered_types:
        entries = groups.get(type_code)
        if not entries:
            continue
        entries.sort(key=lambda e: e[0].lower())
        lines = []
        group_count = 0
        for name, qty, faction, url in entries:
            marker = _aspect_marker(faction, custom_emojis)
            suffix = f" {marker}" if marker else ""
            lines.append(f"{qty}× [{name}]({url}){suffix}")
            group_count += qty
        total += group_count
        label = TYPE_LABELS.get(type_code, type_code.capitalize())
        embed.add_field(
            name=f"{label} ({group_count})",
            value=_truncate_field(lines),
            inline=False,
        )

    if unknown:
        unknown.sort(key=lambda e: e[0])
        lines = [f"{qty}× ⚠ {code}" for code, qty in unknown]
        for _, qty in unknown:
            total += qty
        embed.add_field(name="Unbekannt", value=_truncate_field(lines), inline=False)

    footer_bits = [f"{total} Karten"]
    if deck_id is not None:
        footer_bits.append(f"Deck-ID {deck_id}")
    embed.set_footer(text=" • ".join(footer_bits))

    return embed
