import io
import typing as t
import random as r
import datetime as dt


import discord
import requests
from PIL import Image
from discord.ext import commands
from pixelsort import pixelsort as pxs

def sort_row(row: list) -> list:
    mini = 255*3
    min_index = 0
    for i in range(len(row)):
        try:
            temp = sum(row[i])
        except TypeError:
            temp = row[i]

        if temp < mini:
            mini = temp
            # min_index = i

    sorted_row = row[:min_index]
    sorted_row.sort()
    return sorted_row + row[min_index:]


def pixel_sort(avatar_url: str):
    r = requests.get(avatar_url)
    img = Image.open(io.BytesIO(r.content))
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        row = []
        for x in range(width):
            try:
                row.append(list(pixels[x, y]))
            except TypeError:
                row.append(pixels[x, y])

        row = sort_row(row)
        for x in range(width):
            try:
                pixels[x, y] = tuple(row[x])
            except TypeError:
                pixels[x, y] = row[x]

    sorted_pixels = []
    for y in range(height):
        for x in range(width):
            sorted_pixels.append(pixels[x, y])

    newImg = Image.new('RGB', (width, height))
    newImg.putdata(sorted_pixels)
    return newImg


class Avatar(commands.Cog):
    """Some interesting commands to mess around with a user's profile picture!"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="glitch", description="Messes with the user's pfp to add a glitchy look")
    async def glitch_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        async with ctx.typing():
            glitch = pixel_sort(f"{target.avatar_url}".replace("webp", "png").replace("gif", "png"))
            with io.BytesIO as img_bin:
                glitch.save(img_bin, "PNG")
                img_bin.seek(0)
                await ctx.send(
                    "Here is your a̶̩͇͛̎̽̉̉̚v̷̞͖̣͊̇̆͆͘ą̴̪͈͚̓̊̎͌̽͆̀͒̎̽͒̉̕͘͜ţ̸̲̗͇̯̼̱̱͊͗̋͆̋͐͘a̶̓͗̅͒͑̈́̾͜͝r̸̬̪̬͊̀",
                    file=discord.File(fp=img_bin, filename="image.png"))

    @commands.command(name="sort", description="Sorts the user's pfp.\nThere are 5 sort choices: Lightness, Hue, Intensity, Minimum, and Saturation.\nThresholds describe the bounds of the sort, and are limited to 0 through 1.\nThe angle determines at what angle the sort starts.\nThe randomness controls how accurate the sort is.")
    async def pixel_sort_command(self, ctx: commands.Context, target: t.Optional[discord.User],
                                 sort: t.Optional[str], low_threshold:t.Optional[float],
                                 up_threshold: t.Optional[float], angle: t.Optional[float] = 0,
                                 randomness: t.Optional[float] = 0):
        if target is None:
            target = ctx.author

        if 0 > up_threshold or up_threshold > 1:
            return await ctx.send("The upper threshold must be within 0 and 1!")
        if 0 > low_threshold or low_threshold > 1:
            return await ctx.send("The lower threshold must be within 0 and 1!")

        sort = sort.lower()
        from pixelsort.sorting import choices
        choices = list(choices.keys())
        if sort is None:
            sort = r.choice(choices)
        elif sort not in choices:
            return await ctx.send("You have to choose one of the viable sorts! " + ", ".join(choices).capitalize())

        async with ctx.typing():
            re = requests.get(f"{target.avatar_url}".replace("webp", "png").replace("gif", "png"))
            img = Image.open(io.BytesIO(re.content))
            sortedImg = pxs(img, lower_threshold=low_threshold if low_threshold is not None else 0.0,
                            upper_threshold=up_threshold if up_threshold is not None else 1.0,
                            sorting_function=sort, angle=abs(angle), randomness=abs(randomness))

            with io.BytesIO as img_bin:
                sortedImg.seek(img_bin, "PNG")
                img_bin.seek(0)
                await ctx.send("Here is your sorted profile!",
                    file=discord.File(fp=img_bin, filename="image.png"))

    @commands.command(name="pixelate", description="Pixelates the user's profile picture.")
    async def pixelate_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Pixelate!",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/pixelate")
        embed.set_image(url=f"https://some-random-api.ml/canvas/pixelate?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="blur", description="Blurs the user's profile picture.")
    async def blur_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Blur!",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/blur")
        embed.set_image(url=f"https://some-random-api.ml/canvas/blur?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="simp", aliases=["simpcard"], description="Calls the mentioned a user a simp.")
    async def simpcard_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="SIMP!",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/simpcard")
        embed.set_image(url=f"https://some-random-api.ml/canvas/simpcard?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="horny", description="Proves the mentioned user is a horny bastard.")
    async def horny_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Horny.",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/horny")
        embed.set_image(url=f"https://some-random-api.ml/canvas/horny?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="Lolice", description="Calls the loli police on a user.")
    async def lolice_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Lolice!",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/lolice")
        embed.set_image(url=f"https://some-random-api.ml/canvas/lolice?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="gay-bg", description="Adds a gay border to a user's profile picture.")
    async def pixelate_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="G A Y!",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/lgbt")
        embed.set_image(url=f"https://some-random-api.ml/canvas/lgbt?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="pansexual-bg", description="Adds a pansexual border to a user's profile picture.")
    async def pan_the_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Pan 🍳",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/pansexual")
        embed.set_image(url=f"https://some-random-api.ml/canvas/pansexual?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="nonbinary-bg", description="Adds a nonbinary border to a user's profile picture.")
    async def nonbinary_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Nonbinary",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/nonbinary")
        embed.set_image(url=f"https://some-random-api.ml/canvas/nonbinary?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="lesbian-bg", description="Adds a lesbian border to a user's profile picture.")
    async def lesbian_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Lesbian",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/lesbian")
        embed.set_image(url=f"https://some-random-api.ml/canvas/lesbian?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="bisexual-bg", description="Adds a bisexual border to a user's profile picutre.")
    async def bisexual_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Bisexual",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/bisexual")
        embed.set_image(url=f"https://some-random-api.ml/canvas/bisexual?avatar={target.avatar_url}")
        await ctx.send(embed=embed)

    @commands.command(name="trans-bg", description="Adds a trans order to a user's profile picture.")
    async def transgender_avatar_command(self, ctx: commands.Context, target: t.Optional[discord.User]):
        if target is None:
            target = ctx.author

        embed = discord.Embed(title="Transgender",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: some-random-api.ml/canvas/transgender")
        embed.set_image(url=f"https://some-random-api.ml/canvas/transgender?avatar={target.avatar_url}")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Avatar(bot))
