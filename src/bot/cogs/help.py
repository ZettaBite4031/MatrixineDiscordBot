from typing import Optional
import datetime as dt

import discord
from discord import Embed
from discord.ext.menus import MenuPages, ListPageSource
from discord.ext.commands import command, Cog
from discord.utils import get

from src.bot.bot import MatrixineBot


def syntax(Command):
    cmd_and_aliases = "|".join([str(Command), *Command.aliases])
    params = []

    for key, value in Command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(value) else f"<{key}>")

    params = " ".join(params)

    return f'`{cmd_and_aliases}{f" {params}" if params != "" else ""}`'


class HelpMenu(ListPageSource):
    def __init__(self, ctx, data, cog, bot):
        self.ctx = ctx
        self.bot = bot
        self.cog = cog
        super().__init__(data, per_page=3)

    async def write_page(self, menu, fields=[]):
        offset = (menu.current_page * self.per_page) + 1
        len_data = len(self.entries)

        embed = Embed(title=f"Help {self.cog}",
                      description=f"Welcome to the Matrixine help menu!\nPrefix is {self.bot.PREFIX}",
                      colour=self.bot.COLOR)
        embed.set_thumbnail(url=self.ctx.guild.me.avatar_url)
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset + self.per_page - 1):,} of {len_data:,} commands.")

        for value, name in fields:
            embed.add_field(name=name, value=f"**{value}**", inline=False)

        return embed

    async def format_page(self, menu, entries):
        fields = []

        for entry in entries:
            fields.append((entry.description or "No description", syntax(entry)))

        return await self.write_page(menu, fields)


class Help(Cog):
    """Handles displaying the interactive help menu."""
    def __init__(self, bot: MatrixineBot):
        self.bot = bot
        self.bot.remove_command("help")

    async def cmd_help(self, ctx, command):
        embed = Embed(title=f"Help with `{command}`",
                      description=syntax(command),
                      colour=self.bot.COLOR)
        embed.add_field(name="Command description", value=command.description if command.description else "No description", inline=False)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=embed)

    @command(name="help", aliases=['h'], description="Shows this mess!")
    async def show_help(self, ctx, module: Optional[str], command: Optional[str]):
        """Shows this message."""

        # prefix = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})["server_prefix"]
        prefix = "M!"

        if module is None:
            embed = discord.Embed(
                title="Welcome to the Matrxine Help Menu!",
                description=f"Use `{prefix}help module` to gain more information about that module!\nThe prefix is case insensitive.",
                colour=self.bot.COLOR,
                timestamp=dt.datetime.utcnow()
            )
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            embed.add_field(name="About", value=f"*Matrixine* is developed in Discord.py v1.7.3 by {self.bot.OWNER_UN}\n\
                                                *{self.bot.BOT_INFO.name}* is running on {self.bot.VERSION}", inline=False)
            value = []
            for cog in self.bot.cogs:
                value.append(f"`{cog}`: {self.bot.cogs[cog].__doc__ if self.bot.cogs[cog].__doc__ else 'No description'}")
                msg = "\n".join(value)
            embed.add_field(name="Modules", value=msg, inline=False)
            await ctx.send(embed=embed)

        elif module:
            cog = module.capitalize()
            if cog in self.bot.cogs and command is None:
                if self.bot.get_cog(cog).get_commands():
                    menu = MenuPages(source=HelpMenu(ctx, list(self.bot.get_cog(cog).get_commands()), cog, self.bot),
                                     delete_message_after=True,
                                     timeout=60.0)
                    await menu.start(ctx)

                elif not self.bot.get_cog(cog).get_commands():
                    embed = discord.Embed(
                        title=f"Help {cog}!",
                        description=f"{self.bot.cogs[cog].__doc__ if self.bot.cogs[cog].__doc__ else 'No description.'}\n",
                        colour=self.bot.COLOR,
                        timestamp=dt.datetime.utcnow()
                    )
                    embed.set_thumbnail(url=self.bot.user.avatar_url)
                    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                    embed.add_field(name="This module has no commands.", value="This module is purely functional and contains no commands.", inline=False)
                    await ctx.send(embed=embed)

            elif cog in self.bot.cogs and (cmd := get(self.bot.commands, name=command)):
                await self.cmd_help(ctx, cmd)

            elif cog not in self.bot.cogs:
                await ctx.send("That module does not exist.")


def setup(bot):
    bot.add_cog(Help(bot))