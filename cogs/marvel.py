import discord
from discord.ext import commands
from card_formatter import build_embed, TYPE_LABELS

MAX_SELECT = 25  # Discord-Limit für Select-Menüs


def _card_label(card: dict) -> str:
    """Short label for a card: name + optional subtitle."""
    name = card.get("name") or card.get("real_name", "?")
    subname = card.get("subname")
    unique = "★ " if card.get("is_unique") else ""
    label = f"{unique}{name}"
    if subname:
        label += f" - {subname}"
    return label[:100]


def _card_description(card: dict) -> str:
    """One-line description for Select menu: type + faction."""
    type_label  = TYPE_LABELS.get(card.get("type_code", ""), card.get("type_code", ""))
    faction     = card.get("faction_name", "")
    pack        = card.get("pack_name", "")
    parts = [type_label]
    if faction and faction.lower() not in ("hero", "villain", "encounter",
                                           card.get("type_code", "")):
        parts.append(faction)
    if pack:
        parts.append(pack)
    return " · ".join(parts)[:100]


class CardSelectView(discord.ui.View):
    def __init__(self, matches: list[dict], requester_id: int):
        super().__init__(timeout=60)
        self.requester_id = requester_id

        options = [
            discord.SelectOption(
                label=_card_label(c),
                description=_card_description(c),
                value=str(i),
            )
            for i, c in enumerate(matches)
        ]

        select = discord.ui.Select(
            placeholder="Karte auswählen ...",
            options=options,
        )
        select.callback = self._on_select
        self.select = select
        self.matches = matches
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "Nur die Person, die gesucht hat, darf eine Karte auswählen.",
                ephemeral=True,
            )
            return

        idx = int(self.select.values[0])
        card = self.matches[idx]
        embed = build_embed(card)

        # Disable select after choice
        self.select.disabled = True
        await interaction.response.edit_message(
            content=None, embed=None, view=self
        )
        await interaction.followup.send(embed=embed)
        self.stop()

    async def on_timeout(self):
        self.select.disabled = True
        # Can't edit without a reference to the message here;
        # the message will simply become unresponsive after 60 s.


class Marvel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        content = message.content.strip()
        if not content.lower().startswith("!de:"):
            return

        query = content[4:].strip()
        if not query:
            await message.channel.send(
                "Bitte einen Kartennamen angeben, z.B. `!de:Tigra`"
            )
            return

        async with message.channel.typing():
            try:
                cards = await self.bot.get_de_cards()
            except Exception as e:
                await message.channel.send(f"Fehler beim Laden der Karten: {e}")
                return

            query_lower = query.lower()
            matches = [
                c for c in cards
                if query_lower in (c.get("name") or "").lower()
                or query_lower in (c.get("real_name") or "").lower()
            ]

        if not matches:
            await message.channel.send(
                f'Keine deutsche Karte gefunden, die "{query}" enthaelt.'
            )
            return

        # Single result → direkt anzeigen
        if len(matches) == 1:
            await message.channel.send(embed=build_embed(matches[0]))
            return

        # Zu viele Treffer → Hinweis ohne Auswahl
        if len(matches) > MAX_SELECT:
            await message.channel.send(
                f"**{len(matches)} Treffer** fuer \"{query}\" - bitte den Namen genauer angeben.\n"
                f"Beispiele: "
                + ", ".join(
                    f"`!de:{c.get('name') or c.get('real_name', '?')}`"
                    for c in matches[:5]
                )
            )
            return

        # Mehrere Treffer → Select-Menü
        view = CardSelectView(matches, message.author.id)
        await message.channel.send(
            f'**{len(matches)} Treffer** fuer "{query}" - bitte eine Karte waehlen:',
            view=view,
        )


async def setup(bot):
    await bot.add_cog(Marvel(bot))
