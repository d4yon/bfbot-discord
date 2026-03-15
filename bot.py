import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents
        )

    async def setup_hook(self):
        await self.load_extension("cogs.fun")
        await self.load_extension("cogs.pause")
        await self.tree.sync()
        print("✅ Slash commands synchronisées !")

    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.user}")


async def main():
    bot = Bot()
    await bot.start(TOKEN)


asyncio.run(main())
