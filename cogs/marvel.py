import re
import asyncio
import discord
from discord.ext import commands
from card_formatter import build_embed, TYPE_LABELS, search_cards

PAGE_SIZE = 20


def _card_label(card: dict) -> str:
    name = card.get("name") or card.get("real_name", "?")
    subname = card.get("subname")
    unique = "★ " if card.get("is_unique") else ""
    label = f"{unique}{name}"
    if card.get("stage"):
        label += f" ({card['stage']})"
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


class CardSelectView(discord.ui.View):
    def __init__(
        self,
        matches: list[dict],
        offset: int,
        requester_id: int,
        future: asyncio.Future | None = None,
    ):
        super().__init__(timeout=60)
        self.matches      = matches
        self.offset       = offset
        self.requester_id = requester_id
        self.future       = future

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
            new_view = CardSelectView(self.matches, max(0, self.offset - PAGE_SIZE),
                                      self.requester_id, self.future)
            await interaction.response.edit_message(view=new_view)
            return

        if value == "__next__":
            new_view = CardSelectView(self.matches, self.offset + PAGE_SIZE,
                                      self.requester_id, self.future)
            await interaction.response.edit_message(view=new_view)
            return

        card = self.matches[int(value)]
        self.select.disabled = True

        if self.future and not self.future.done():
            # Multi-Modus: Future auflösen, Bestätigung anzeigen
            name = card.get("name") or card.get("real_name", "?")
            await interaction.response.edit_message(
                content=f"✓ *{name}* ausgewählt.", view=None
            )
            self.future.set_result(card)
        else:
            # Einzel-Modus: Embed direkt senden
            await interaction.response.edit_message(content=None, view=self)
            await interaction.followup.send(embed=build_embed(card))

        self.stop()

    async def on_timeout(self):
        self.select.disabled = True
        if self.future and not self.future.done():
            self.future.cancel()


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

        # Einzelne Abfrage: bisheriges Verhalten
        if len(queries) == 1:
            await self._handle_single(message, cards, queries[0].strip())
            return

        # Mehrere Abfragen: erst alle lösen, dann gemeinsam anzeigen
        await self._handle_multi(message, cards, [q.strip() for q in queries])

    async def _handle_single(self, message: discord.Message, cards: list, query: str):
        if len(query) < 3:
            await message.channel.send(f'"{query}": Bitte mindestens 3 Buchstaben angeben.')
            return

        matches = search_cards(cards, query)
        if not matches:
            await message.channel.send(f'Keine deutsche Karte gefunden für "{query}".')
            return

        if len(matches) == 1:
            await message.channel.send(embed=build_embed(matches[0]))
            return

        view = CardSelectView(matches, offset=0, requester_id=message.author.id)
        await message.channel.send(
            f'**{len(matches)} Treffer** für "{query}" – bitte eine Karte wählen:',
            view=view,
        )

    async def _handle_multi(self, message: discord.Message, cards: list, queries: list[str]):
        loop = asyncio.get_event_loop()

        # Slot: resolved card | None (error/timeout) | asyncio.Future (pending)
        slots: list[dict | None | asyncio.Future] = []

        for query in queries:
            if len(query) < 3:
                await message.channel.send(f'"{query}": Bitte mindestens 3 Buchstaben angeben.')
                slots.append(None)
                continue

            matches = search_cards(cards, query)
            if not matches:
                await message.channel.send(f'Keine deutsche Karte gefunden für "{query}".')
                slots.append(None)
                continue

            if len(matches) == 1:
                slots.append(matches[0])
                continue

            future: asyncio.Future = loop.create_future()
            view = CardSelectView(matches, offset=0, requester_id=message.author.id,
                                  future=future)
            await message.channel.send(
                f'**{len(matches)} Treffer** für "{query}" – bitte eine Karte wählen:',
                view=view,
            )
            slots.append(future)

        # Auf alle offenen Auswahlen warten
        for i, slot in enumerate(slots):
            if isinstance(slot, asyncio.Future):
                try:
                    slots[i] = await asyncio.wait_for(asyncio.shield(slot), timeout=120)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    slots[i] = None
                    await message.channel.send(
                        f'Zeitüberschreitung für „{queries[i]}" – Karte übersprungen.'
                    )

        # Alle gefundenen Karten in Originalreihenfolge anzeigen
        for card in slots:
            if card is not None:
                await message.channel.send(embed=build_embed(card))


async def setup(bot):
    await bot.add_cog(Marvel(bot))
