import re
import asyncio
import discord
from discord.ext import commands
from card_formatter import build_embed, TYPE_LABELS, search_cards
from rulebook_search import search_rules

PAGE_SIZE = 20
RULE_COLOR = 0x8B0000
RULEBOOK_URL = "https://asmodee-resources.azureedge.net/media/germanyprod/Regeln/marvel-champions-lcg-4015566029613-referenzhandbuch-v1-7de.pdf"


def _split_text(text: str, limit: int) -> list[str]:
    parts = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    parts.append(text)
    return parts


def _apply_custom_emojis(text: str, custom_emojis: dict) -> str:
    return re.sub(
        r":(\w+):",
        lambda m: custom_emojis.get(m.group(1).lower(), m.group(0)),
        text,
    )


def build_rule_embeds(entry: dict, custom_emojis: dict | None = None) -> list[discord.Embed]:
    title = entry["title"].title()
    text = entry.get("text", "")
    if custom_emojis:
        title = _apply_custom_emojis(title, custom_emojis)
        text = _apply_custom_emojis(text, custom_emojis)
    page = entry.get("page")
    url = RULEBOOK_URL + (f"#page={page}" if page else "")
    footer = f"\n\n[Quelle: Online-Referenzhandbuch v1.7de]({url})" + (f" · Seite {page}" if page else "")

    # Try to fit everything in one embed
    if len(text + footer) <= 4096:
        return [discord.Embed(title=title, description=text + footer, color=RULE_COLOR)]

    # Split text into pages, attach footer to the last
    pages = _split_text(text, 4096)
    if len(pages[-1] + footer) <= 4096:
        pages[-1] += footer
    else:
        pages.append(footer.lstrip())

    total = len(pages)
    embeds = []
    for i, page in enumerate(pages):
        t = title if total == 1 else f"{title} ({i + 1}/{total})"
        embeds.append(discord.Embed(title=t, description=page, color=RULE_COLOR))
    return embeds


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
        custom_emojis: dict | None = None,
    ):
        super().__init__(timeout=60)
        self.matches       = matches
        self.offset        = offset
        self.requester_id  = requester_id
        self.future        = future
        self.custom_emojis = custom_emojis or {}

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
                                      self.requester_id, self.future, self.custom_emojis)
            await interaction.response.edit_message(view=new_view)
            return

        if value == "__next__":
            new_view = CardSelectView(self.matches, self.offset + PAGE_SIZE,
                                      self.requester_id, self.future, self.custom_emojis)
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
            await interaction.followup.send(embed=build_embed(card, self.custom_emojis))

        self.stop()

    async def on_timeout(self):
        self.select.disabled = True
        if self.future and not self.future.done():
            self.future.cancel()


class RuleRefView(discord.ui.View):
    def __init__(self, refs: list[str], custom_emojis: dict):
        super().__init__(timeout=300)
        self.custom_emojis = custom_emojis
        self.message: discord.Message | None = None

        for ref in refs[:25]:
            btn = discord.ui.Button(label=ref.title()[:80], style=discord.ButtonStyle.secondary)
            btn.callback = self._make_callback(ref)
            self.add_item(btn)

    def _make_callback(self, ref: str):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            matches = search_rules(ref)
            if not matches:
                await interaction.followup.send(f'Keine Regel gefunden für „{ref}".', ephemeral=True)
                return
            entry = matches[0] if len(matches) == 1 else None
            if entry is None:
                view = RuleSelectView(matches, interaction.user.id, self.custom_emojis)
                await interaction.followup.send(
                    f'**{len(matches)} Treffer** für „{ref}" – bitte eine Regel wählen:',
                    view=view,
                )
                return
            await _send_rule(interaction.followup.send, entry, self.custom_emojis)
        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


async def _send_rule(send_fn, entry: dict, custom_emojis: dict):
    embeds = build_rule_embeds(entry, custom_emojis)
    refs = entry.get("references") or []
    ref_view = RuleRefView(refs, custom_emojis) if refs else None
    for embed in embeds[:-1]:
        await send_fn(embed=embed)
    msg = await send_fn(embed=embeds[-1], view=ref_view)
    if ref_view and msg:
        ref_view.message = msg


class RuleSelectView(discord.ui.View):
    def __init__(self, matches: list[dict], requester_id: int, custom_emojis: dict | None = None):
        super().__init__(timeout=60)
        self.matches       = matches
        self.requester_id  = requester_id
        self.custom_emojis = custom_emojis or {}

        options = [
            discord.SelectOption(label=e["title"].title()[:100], value=str(i))
            for i, e in enumerate(matches[:25])
        ]
        select = discord.ui.Select(placeholder="Regel auswählen …", options=options)
        select.callback = self._on_select
        self.select = select
        self.add_item(select)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "Nur die Person, die gesucht hat, darf eine Regel auswählen.",
                ephemeral=True,
            )
            return

        entry = self.matches[int(self.select.values[0])]
        self.select.disabled = True
        await interaction.response.edit_message(content=None, view=self)
        await _send_rule(interaction.followup.send, entry, self.custom_emojis)
        self.stop()

    async def on_timeout(self):
        self.select.disabled = True


class Marvel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _custom_emojis(self) -> dict:
        return {e.name: str(e) for e in self.bot.emojis}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        rule_queries = re.findall(r'\[\((.+?)\)\]', message.content)
        if rule_queries:
            for query in rule_queries:
                await self._handle_rule(message, query.strip())
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

    async def _handle_rule(self, message: discord.Message, query: str):
        if len(query) < 2:
            await message.channel.send(f'"{query}": Bitte mindestens 2 Buchstaben angeben.')
            return

        matches = search_rules(query)
        if not matches:
            await message.channel.send(f'Keine Regel gefunden für „{query}".')
            return

        emojis = self._custom_emojis()
        if len(matches) == 1:
            await _send_rule(message.channel.send, matches[0], emojis)
            return

        view = RuleSelectView(matches, requester_id=message.author.id, custom_emojis=emojis)
        await message.channel.send(
            f'**{len(matches)} Treffer** für „{query}" – bitte eine Regel wählen:',
            view=view,
        )

    async def _handle_single(self, message: discord.Message, cards: list, query: str):
        if len(query) < 3:
            await message.channel.send(f'"{query}": Bitte mindestens 3 Buchstaben angeben.')
            return

        matches = search_cards(cards, query)
        if not matches:
            await message.channel.send(f'Keine deutsche Karte gefunden für "{query}".')
            return

        emojis = self._custom_emojis()
        if len(matches) == 1:
            await message.channel.send(embed=build_embed(matches[0], emojis))
            return

        view = CardSelectView(matches, offset=0, requester_id=message.author.id,
                              custom_emojis=emojis)
        await message.channel.send(
            f'**{len(matches)} Treffer** für "{query}" – bitte eine Karte wählen:',
            view=view,
        )

    async def _handle_multi(self, message: discord.Message, cards: list, queries: list[str]):
        loop = asyncio.get_event_loop()
        emojis = self._custom_emojis()

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
                                  future=future, custom_emojis=emojis)
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
                await message.channel.send(embed=build_embed(card, emojis))


async def setup(bot):
    await bot.add_cog(Marvel(bot))
