import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))


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

        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Slash commands synchronisees !")

    async def on_ready(self):
        print(f"connected as {self.user}")


async def main():
    bot = Bot()
    await bot.start(TOKEN)


asyncio.run(main())
