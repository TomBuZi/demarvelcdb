import re
import discord
from discord.ext import commands
from card_formatter import build_embed, TYPE_LABELS, search_cards

PAGE_SIZE = 20


def _card_label(card: dict) -> str:
    name = card.get("name") or card.get("real_name", "?")
    subname = card.get("subname")
    unique = "★ " if card.get("is_unique") else ""
    label = f"{unique}{name}"
    if subname:
        label += f" - {subname}"
    return label[:100]


def _card_description(card: dict) -> str:
    type_label = TYPE_LABELS.get(card.get("type_code", ""), card.get("type_code", ""))
    faction    = card.get("faction_name", "")
    pack       = card.get("pack_name", "")
    parts = [type_label]
    if faction and faction.lower() not in ("hero", "villain", "encounter",
                                           card.get("type_code", "")):
        parts.append(faction)
    if pack:
        parts.append(pack)
    return " · ".join(parts)[:100]


def _build_select_view(matches: list[dict], offset: int, requester_id: int) -> "CardSelectView":
    return CardSelectView(matches, offset, requester_id)


class CardSelectView(discord.ui.View):
    def __init__(self, matches: list[dict], offset: int, requester_id: int):
        super().__init__(timeout=60)
        self.matches      = matches
        self.offset       = offset
        self.requester_id = requester_id

        page    = matches[offset:offset + PAGE_SIZE]
        total   = len(matches)
        options = []

        if offset > 0:
            prev_count = min(offset, PAGE_SIZE)
            options.append(discord.SelectOption(
                label=f"⬅ Die vorherigen {prev_count} Ergebnisse anzeigen...",
                value="__prev__",
            ))

        for i, c in enumerate(page):
            options.append(discord.SelectOption(
                label=_card_label(c),
                description=_card_description(c),
                value=str(offset + i),
            ))

        remaining = total - offset - PAGE_SIZE
        if remaining > 0:
            next_count = min(remaining, PAGE_SIZE)
            options.append(discord.SelectOption(
                label=f"➡ Die nächsten {next_count} Ergebnisse anzeigen...",
                value="__next__",
            ))

        select = discord.ui.Select(placeholder="Karte auswählen ...", options=options)
        select.callback = self._on_select
        self.select = select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "Nur die Person, die gesucht hat, darf eine Karte auswählen.",
                ephemeral=True,
            )
            return

        value = self.select.values[0]

        if value == "__prev__":
            new_offset = max(0, self.offset - PAGE_SIZE)
            new_view = CardSelectView(self.matches, new_offset, self.requester_id)
            await interaction.response.edit_message(view=new_view)
            return

        if value == "__next__":
            new_offset = self.offset + PAGE_SIZE
            new_view = CardSelectView(self.matches, new_offset, self.requester_id)
            await interaction.response.edit_message(view=new_view)
            return

        card = self.matches[int(value)]
        embed = build_embed(card)
        self.select.disabled = True
        await interaction.response.edit_message(content=None, embed=None, view=self)
        await interaction.followup.send(embed=embed)
        self.stop()

    async def on_timeout(self):
        self.select.disabled = True


class Marvel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        queries = re.findall(r'\[\[(.+?)]]', message.content)
        if not queries:
            return

        async with message.channel.typing():
            try:
                cards = await self.bot.get_de_cards()
            except Exception as e:
                await message.channel.send(f"Fehler beim Laden der Karten: {e}")
                return

            for query in queries:
                query = query.strip()
                if len(query) < 3:
                    await message.channel.send(
                        f'"{query}": Bitte mindestens 3 Buchstaben angeben.'
                    )
                    continue

                matches = search_cards(cards, query)

                if not matches:
                    await message.channel.send(
                        f'Keine deutsche Karte gefunden für "{query}".'
                    )
                    continue

                if len(matches) == 1:
                    await message.channel.send(embed=build_embed(matches[0]))
                    continue

                view = CardSelectView(matches, offset=0, requester_id=message.author.id)
                await message.channel.send(
                    f'**{len(matches)} Treffer** für "{query}" – bitte eine Karte wählen:',
                    view=view,
                )


async def setup(bot):
    await bot.add_cog(Marvel(bot))
