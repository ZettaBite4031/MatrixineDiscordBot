import typing as t
import datetime as dt

import discord
from discord.ext import commands

from src.bot.bot import MatrixineBot

class Logging(commands.Cog):
    """Handles logging events and commands"""

    def __init__(self, bot: MatrixineBot):
        self.bot = bot
        self.database = self.bot.MONGO_DB
        self.leveling = self.database["Leveling"]
        self.guilds = self.database["Guilds"]

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        pass

    @commands.Cog.listener()
    async def on_message_delete(self, before, after):
        pass


def setup(bot: MatrixineBot):
    bot.add_cog(Logging(bot))