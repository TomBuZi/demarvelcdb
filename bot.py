import os
import asyncio
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

DE_API_BASE = "https://de.marvelcdb.com/api/public"


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
            if self._cards_cache is None:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{DE_API_BASE}/cards/") as resp:
                        resp.raise_for_status()
                        self._cards_cache = await resp.json(content_type=None)
            return self._cards_cache


def main():
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN nicht gesetzt. Bitte .env-Datei anlegen.")
    bot = MarvelBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
