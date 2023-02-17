import random as r
import datetime as dt
import typing as t

import discord
from discord.ext import commands

class Filters(commands.Cog):
    """Filter commands for a user's pfp."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="Overlays",
                      description="Adds overlays onto the specified user's avatar; if none is provided, it will use the caller's profile.")
    async def overlay_group(self, ctx, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        overlays = ["gay", "glass", "wasted", "passed", "jail", "comrade", "triggered"]
        overlay = r.choice(overlays)
        url = f"https://some-random-api.ml/canvas/{overlay}?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/{overlay}")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="gay")
    async def gay_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/gay?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/gay")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="glass")
    async def glass_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/glass?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/glas")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="wasted")
    async def wasted_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/wasted?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/wasted")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="passed")
    async def passed_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/passed?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/passed")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="jail")
    async def jail_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/jail?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/jail")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="comrade")
    async def comrade_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/comrade?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/comrade")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="triggered")
    async def triggered_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/triggered?avatar={target.avatar_url}".replace(".webp", ".png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/triggered")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="filter")
    async def filter_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        choices = ["greyscale", "invert", "invertgreyscale", "sepia", "red", "green", "blue", "blurple", "blurple2"]
        filter = r.choice(choices)
        url = f"https://some-random-api.ml/canvas/{filter}?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=f"{target.display_name} {filter.capitalize()}",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/{filter}")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="greyscale")
    async def greyscale_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/greyscale?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/greyscale")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="invert")
    async def invert_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/invert?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/invert")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="invertgreyscale")
    async def invertgreyscale_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/invertgreyscale?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/invertgreyscale")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="sepia")
    async def sepia_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/sepia?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/sepia")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="red")
    async def red_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/red?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/red")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="green")
    async def green_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/green?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/green")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="blue")
    async def blue_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/blue?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/blue")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="blurple")
    async def blurple_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/blurple?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/blurple")
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(name="blurple2")
    async def blurple2_overlay(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author
        url = f"https://some-random-api.ml/canvas/blurple2?avatar={target.avatar_url}".replace("webp", "png")
        embed = discord.Embed(title=target.display_name,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f"API: some-random-api.ml/canvas/blurple2")
        embed.set_image(url=url)
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Filters(bot))