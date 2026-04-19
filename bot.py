import os
import asyncio
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

DE_API_BASE  = "https://de.marvelcdb.com/api/public"
GITHUB_RAW   = "https://raw.githubusercontent.com/zzorba/marvelsdb-json-data/master"
DE_TRANS_BASE = f"{GITHUB_RAW}/translations/de/pack"
EN_PACK_BASE  = f"{GITHUB_RAW}/pack"

_DE_OVERLAY_FIELDS = ("name", "text", "traits", "flavor", "subname")


async def _fetch_json(session: aiohttp.ClientSession, url: str) -> list | dict | None:
    try:
        async with session.get(url) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            return await resp.json(content_type=None)
    except Exception:
        return None


class MarvelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self._cards_cache: list | None = None
        self._cache_lock = asyncio.Lock()

    async def setup_hook(self):
        await self.load_extension("cogs.marvel")

    async def get_de_cards(self) -> list:
        async with self._cache_lock:
            if self._cards_cache is not None:
                return self._cards_cache

            async with aiohttp.ClientSession() as session:
                # Spielerkarten von der deutschen API
                async with session.get(f"{DE_API_BASE}/cards/") as resp:
                    resp.raise_for_status()
                    player_cards = await resp.json(content_type=None)

                # Encounter-Karten deaktiviert (zu langsam beim Start)
                # packs_data = await _fetch_json(session, f"{DE_API_BASE}/packs/") or []
                # pack_map = {p["code"]: p["name"] for p in packs_data}
                # encounter_tasks = [
                #     self._load_encounter_pack(session, code, name)
                #     for code, name in pack_map.items()
                # ]
                # encounter_results = await asyncio.gather(*encounter_tasks)
                # encounter_cards = [c for pack in encounter_results for c in pack]
                encounter_cards = []

            self._cards_cache = player_cards + encounter_cards
            return self._cards_cache

    async def _load_encounter_pack(
        self, session: aiohttp.ClientSession, pack_code: str, pack_name: str
    ) -> list:
        en_cards = await _fetch_json(session, f"{EN_PACK_BASE}/{pack_code}_encounter.json")
        if not en_cards:
            return []

        de_entries = await _fetch_json(session, f"{DE_TRANS_BASE}/{pack_code}_encounter.json") or []
        de_map = {c["code"]: c for c in de_entries}

        result = []
        for card in en_cards:
            card = dict(card)
            card.setdefault("pack_code",   pack_code)
            card.setdefault("pack_name",   pack_name)
            card.setdefault("faction_code", "encounter")
            card.setdefault("faction_name", "Encounter")
            card.setdefault("imagesrc",    f"/bundles/cards/{card['code']}.png")
            card.setdefault("url",         f"https://de.marvelcdb.com/card/{card['code']}")

            # Englische Originale sichern
            card["real_name"]   = card.get("name", "")
            card["real_text"]   = card.get("text", "")
            card["real_traits"] = card.get("traits", "")

            # Deutsche Übersetzung drüberlegen
            if card["code"] in de_map:
                for field in _DE_OVERLAY_FIELDS:
                    if field in de_map[card["code"]]:
                        card[field] = de_map[card["code"]][field]

            result.append(card)

        return result


def main():
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN nicht gesetzt. Bitte .env-Datei anlegen.")
    bot = MarvelBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
