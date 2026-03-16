import discord
from discord.ext import commands
from discord import app_commands
from .llm import LLM
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_member = None
        self.llm = LLM()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Bienvenue {member.mention} !')

    @app_commands.command(name="hello", description="Dit bonjour !") 
    async def hello(self, interaction: discord.Interaction):
        if self._last_member is None or self._last_member.id != interaction.user.id:
            await interaction.response.send_message(f'Bonjour {interaction.user.name} !')
        else:
            await interaction.response.send_message(f'Rebonjour {interaction.user.name} !')

        self._last_member = interaction.user

    @app_commands.command(name="ask", description="Pose une question au LLM")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()

        history = [
            SystemMessage(content="Tu es un assistant utile et sympa sur Discord."),
            HumanMessage(content=question)
        ]

        response = await self.llm.ask(history)
        await interaction.followup.send(f"{interaction.user.mention} {response.content}")


async def setup(bot):
    await bot.add_cog(Fun(bot))