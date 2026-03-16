import discord
from discord.ext import commands
#from llm import LangChainBot

class Quiz(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        #self.llm = LangChainBot()

    @commands.Cog.listener()
    async def on_message(self,message):

        if message.author == self.bot.user:
            return
        if message.content.startswith(('!', '/')):
            return

        uid = message.author.id
        response = await self.llm.generate_response(uid,message.content)
        await message.channel.send(response)

    @commands.command(name='quiz',
                 help='Generate question based on user theme choice(Comptia Security+ certification)')
    async def quiz(self,ctx,theme):
        uid = ctx.author.id
        response = await self.llm.generate_response(uid,theme)
        await ctx.send(response)

async def setup(bot):
    await bot.add_cog(Quiz(bot))
