import base64
import json
import pathlib
import random as r
import typing as t
import datetime as dt

import aiohttp
import discord
from discord.ext import commands


def _count_generator(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


class Fun(commands.Cog):
    """Just random fun commands that add some personality and chill to the bot."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello", aliases=["hi", "hey", "hiya", "sup"], description="Will greet and mention the user executing the command.")
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    async def greet_command(self, ctx):
        """Will greet and mention the user executing the command."""
        responses = ["Hello", "Hi", "What's up", "Hiya"]
        response = r.choice(responses)
        await ctx.send(f"{response}, {ctx.author.mention}!")

    @commands.command(name="dice", aliases=['roll'], description="Rolls dice. Syntax: `Number of dice`d`Value of each dice`. Summed will determine whether or not it shows the addition of all the die.")
    async def roll_dice_command(self, ctx, die_string: str, summed: str = "yes"):
        dice, value = (int(term) for term in die_string.split("d"))
        if dice <= 0 or value <= 0:
            return await ctx.send("Please choose a value above 0!")
        if dice > 100 or value > 10000:
            return await ctx.send("Please choose smaller values!")
        rolls = [r.randint(1, value) for _ in range(dice)]
        response = sum(rolls) if summed.lower() == "yes" else " + ".join(
            [str(roll) for roll in rolls]) + f" = {sum(rolls)}"
        await ctx.send(response)

    @roll_dice_command.error
    async def roll_dice_error(self, ctx, exc):
        if isinstance(exc.original, discord.HTTPException):
            await ctx.send("Too many dice rolled! Discord message length hit!")

    @commands.command(name="slap", alises=["hit"], description="It does exactly what you think it does")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def slap_member_command(self, ctx, member: discord.Member, *, reason: t.Optional[str] = "no reason"):
        choices = ["slapped", "hit", "punched", "socked", "bitch-slapped", "brutally assaulted"]
        choice = r.choice(choices)
        await ctx.send(f"{ctx.author.mention} {choice} {member.mention} for {reason}")

    @slap_member_command.error
    async def slap_member_error(self, ctx, exc):
        if isinstance(exc, commands.BadArgument):
            await ctx.send("That member does not exit!")

        if isinstance(exc, commands.MissingRequiredArgument):
            await ctx.send("You need to specify a member!")

    @commands.command(name="echo", description="Echos the phrase put into it.")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def echo_message_command(self, ctx, *, message):
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command(name="animalFact", aliases=["afact"], description="Reveals a fact about 9 separate animals! Dogs, cats, pandas, birds, foxes, koalas, red pandas, racoons, and kangaroos!")
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def animal_fact_command(self, ctx, animal: t.Optional[str]):
        if animal is None:
            choices = ["dog", "cat", "panda", "bird", "fox", "koala", "red_panda", "raccoon", "kangaroo"]
            animal = r.choice(choices)

        if animal == "red panda":
            animal = "red_panda"

        url = "https://some-random-api.ml/animal/{}".format(animal)
        async with aiohttp.request("GET", url, headers={}) as resp:
            if resp.status != 200:
                if resp.status == 404:
                    return await ctx.send("The animal, {}, is not featured in the API!".format(animal))
                else:
                    return await ctx.send("API responded with a {} code. Perhaps try again?".format(resp.status))

            data = await resp.json()
            image = data["image"]
            fact = data["fact"]
            embed = discord.Embed(title=f"{animal.capitalize()} fact!",
                                  description=f"**{fact}**",
                                  color=self.bot.COLOR,
                                  timestamp=dt.datetime.utcnow())
            embed.set_image(url=image)
            embed.set_footer(text=f"API: {url[8:]}")
            await ctx.send(embed=embed)

    @animal_fact_command.error
    async def onAnimalFactError(self, ctx, exc):
        pass

    @commands.command(name='animalImage', aliases=["pic", "picture"], description="Show a picture of 9 separate animals! Dogs, cats, pandas, birds, foxes, koalas, red pandas, racoons, and kangaroos!")
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def animal_image_command(self, ctx, animal: t.Optional[str]):
        if animal is None:
            choices = ["dog", "cat", "panda", "bird", "fox", "koala", "red_panda", "raccoon", "kangaroo"]
            animal = r.choice(choices)

        if animal == "red panda":
            animal = "red_panda"

        url = "https://some-random-api.ml/img/{}".format(animal)
        async with aiohttp.request("GET", url, headers={}) as resp:
            if resp.status != 200:
                if resp.status == 404:
                    return await ctx.send("The animal, {}, is not featured in the API!".format(animal))
                else:
                    return await ctx.send("API responded with a {} code. Perhaps try again?".format(resp.status))

            data = await resp.json()
            image = data["image"]
            embed = discord.Embed(title=f"{animal.capitalize().replace('_', ' ')} image!",
                                  color=self.bot.COLOR,
                                  timestamp=dt.datetime.utcnow())
            embed.set_image(url=image)
            embed.set_footer(text=f"API: {url[8:]}")
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @animal_image_command.error
    async def onAnimalImageError(self, ctx, exc):
        pass

    @commands.command(name="Quote", description="Sends a random quote.")
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def quote(self, ctx):
        url = "https://zenquotes.io/api?api=quotes"
        async with aiohttp.request("GET", url, headers={}) as response:
            if response.status == 200:
                data = await response.json()
                data = data[0]
                quote = data["q"]
                author = data["a"]
                embed = discord.Embed(description="{}".format(quote), color=self.bot.COLOR,
                                      timestamp=dt.datetime.utcnow())
                embed.set_author(name="Quote: ", icon_url=ctx.author.avatar_url)
                embed.set_footer(text="Quote by {}".format(author))
                await ctx.send(embed=embed)
            else:
                print(response.status)
                await ctx.send("Something went wrong!")

    @commands.command(name="ping", aliases=["pong", "latency"], description="A check for Matrixine's latency.")
    async def latency(self, ctx):
        await ctx.send(f"Pong! My latency is {(self.bot.latency * 1000):,.2f}ms")

    @commands.command(name="anime", description="Allows the user to hug, wink at, and pat users!")
    async def anime_command(self, ctx, action: t.Optional[str], target: t.Optional[discord.User]):
        if action is None:
            action = r.choice(["wink", "pat", "hug"])

        url = "https://some-random-api.ml/animu/{}".format(action)
        async with aiohttp.request("GET", url, headers={}) as resp:
            if resp.status != 200:
                if resp.status == 404:
                    return await ctx.send("The action, {}, is not featured in the API!".format(action))
                else:
                    return await ctx.send("API responded with a {} code. Perhaps try again?".format(resp.status))

            if target is None:
                content = f"Don't worry, I'll {action} you, {ctx.author.mention}..."
                title = f"Don't worry, I'll {action} you, {ctx.author.display_name}..."
            else:
                choices = [
                    f"{ctx.author.mention} gave {target.mention} a little bit of a {action}",
                    f"{ctx.author.mention} just {action}ed {'at ' if action == 'wink' else ''} {target.mention}",
                    f"{ctx.author.mention} {action}ed {'at ' if action == 'wink' else ''} {target.mention}"
                ]
                content = r.choice(choices)
                title = action.capitalize() + "!"

            data = await resp.json()
            gif = data["link"]
            embed = discord.Embed(title=title,
                                  color=self.bot.COLOR,
                                  timestamp=dt.datetime.utcnow())
            embed.set_image(url=gif)
            embed.set_footer(text=f"API: {url[8:]}")
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(content, embed=embed)

    @commands.command(name="joke", description="Sends a joke. The devs are not reasonable for how cringe they are.")
    async def send_joke_command(self, ctx):
        url = "https://some-random-api.ml/joke"
        async with aiohttp.request("GET", url, headers={}) as resp:
            if resp.status != 200:
                return await ctx.send("API responded with a {} code. Perhaps try again?".format(resp.status))

            data = await resp.json()
            joke = data["joke"]
            embed = discord.Embed(title="You asked for this.",
                                  description=joke,
                                  color=self.bot.COLOR,
                                  timestamp=dt.datetime.utcnow())
            embed.set_footer(text=f"API: {url[8:]}")
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(name="pokedex", aliases=["pokemon"], description="Sends the information of a pokemon!")
    async def pokedex_command(self, ctx, pokemon: str):
        pokemon = pokemon.lower()
        url = f"https://some-random-api.ml/pokedex?pokemon={pokemon}"
        async with aiohttp.request("GET", url, headers={}) as resp:
            if resp.status != 200:
                if resp.status == 404:
                    return await ctx.send("Was that a valid pokemon? Make sure you spelled it right!")
                else:
                    return await ctx.send("API responded with a {} code. Perhaps try again?".format(resp.status))

            data = await resp.json()
            name = data["name"]
            ID = data["id"]
            types = data["type"]
            species = data["species"]
            abilities = data["abilities"]
            height = data["height"]
            weight = data['weight']
            base_xp = data["base_experience"]
            gender_distribution = data['gender']
            egg_groups = data["egg_groups"]
            stats = data['stats']
            hp = stats['hp']
            attack = stats["attack"]
            defense = stats["defense"]
            sp_atk = stats['sp_atk']
            sp_def = stats['sp_def']
            speed = stats['speed']
            total = stats['total']
            family = data['family']
            evolution_stage = family['evolutionStage']
            evolution_line = family['evolutionLine']
            sprites = data['sprites']
            normal_img = sprites["normal"]
            animated_img = sprites["animated"]
            description = data['description']
            generation = data["generation"]

            description = \
                f"""
            {name.capitalize()}, ID {ID}, is a {", ".join(types)} {species[0]} pokemon with {", ".join(abilities)} abilities. Standing \
             at {height} and weighing in at {weight}, {name.capitalize()} is a pokemon with {base_xp} base experience and a gender \
             distribution of {" and ".join(gender_distribution)} and is considered to have {", ".join(egg_groups)} egg \
             groups by studiers. {name.capitalize()} has {hp} hp with an attack that deals {attack} damage and a defense of \
{defense}, but has been recorded to have special attacks and defenses that deal {sp_atk} and {sp_def} accordingly, and \
can move at a speed of {speed} for a total of {total}.\nBeing at evolution stage {evolution_stage} of an evolution line \
of {", ".join(evolution_line)}, a description of {name.capitalize()} is one of that {description}\n{name.capitalize()} is generation {generation}.
            """\

            embed = discord.Embed(
                title=name.capitalize(),
                description=description,
                color=self.bot.COLOR,
                timestamp=dt.datetime.utcnow()
            )
            embed.set_image(url=normal_img)
            embed.set_thumbnail(url=animated_img)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f"API: {url[8:][:26]}")
            await ctx.send(embed=embed)

    # @commands.command(name="minecraft", aliases=["mc"], description="Sends the information of a specified Minecraft user!")
    # @commands.cooldown(rate=1, per=20, type=commands.BucketType.user)
    # async def get_minecraft_details(self, ctx, account: str):
    #     account = account.lower()
    #     url = f"https://api.namemc.com/profile/{account}/friends"
    #     Nerfed because Mojang murdered their API

    @commands.command(name="meme", description="Sends meme pog")
    async def meme_command(self, ctx):
        url = "https://some-random-api.ml/meme"
        async with aiohttp.request("GET", url, headers={}) as resp:
            if resp.status != 200:
                return await ctx.send("API responded with a {} code. Perhaps try again?".format(resp.status))

            data = await resp.json()

            embed = discord.Embed(title=f"**{data['caption']}**",
                                  color=self.bot.COLOR,
                                  timestamp=dt.datetime.utcnow())
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f"API: {url[8:]}")
            embed.set_image(url=data["image"])
            await ctx.send(embed=embed)

    @commands.command(name="token", aliases=["genToken"], description="Generates a completely random, unreproducible *fake* bot token.")
    async def generate_bot_token_command(self, ctx):
        seed = r.SystemRandom().randint(ctx.author.id, ctx.author.id * 10)
        url = f"https://some-random-api.ml/bottoken?id={seed}"
        async with aiohttp.request("GET", url, headers={}) as resp:
            if resp.status != 200:
                return await ctx.send("API responded with a {} code. Perhaps try again?".format(resp.status))

            data = await resp.json()
            embed = discord.Embed(title="Bot Token",
                                  description=f"Here is your generated bot token!\n{data['token']}",
                                  color=self.bot.COLOR,
                                  timestamp=dt.datetime.utcnow())
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            embed.set_footer(text=f"*These tokens are all fake.* API: {url[8:26]}")
            await ctx.send(embed=embed)

    @commands.command(name="color", description="Sends an embed with the corresponding hexadecimal color sent in the command.")
    async def hex_to_color_command(self, ctx, hexadecimal: str):
        embed = discord.Embed(title=hexadecimal,
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="API: https://some-random-api.ml/canvas/colorviewer")
        embed.set_image(url=f"https://some-random-api.ml/canvas/colorviewer?hex={hexadecimal.replace('0x','')}")
        await ctx.send(embed=embed)

    @commands.command(name="lines", description="Displays the number of lines in the bot's source code.")
    async def lines_of_code_command(self, ctx):
        cogs = [p.stem for p in pathlib.Path(".").glob("./bot/cogs/*.py")]
        total = 11
        for cog in cogs:
            with open(f"./bot/cogs/{cog}.py", 'rb') as fp:
                c_generator = _count_generator(fp.raw.read)
                count = sum(buffer.count(b'\n') for buffer in c_generator)
                total += count

        with open("./bot/bot.py", 'rb') as fp:
            c_generator = _count_generator(fp.raw.read)
            mainCount = sum(buffer.count(b'\n') for buffer in c_generator)
            total += mainCount

        embed = discord.Embed(title=f"{self.bot.BOT_INFO.name} source code length!",
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Bot developed by "+self.bot.OWNER_UN)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(name="Total length:", value=f"`{total}` lines of code!", inline=False)
        embed.add_field(name="Main File:", value=f"`{mainCount}` lines of code", inline=False)
        embed.add_field(name="**Modules**", value="** **", inline=False)
        for cog in cogs:
            with open(f"./bot/cogs/{cog}.py", 'rb') as fp:
                c_generator = _count_generator(fp.raw.read)
                count = sum(buffer.count(b'\n') for buffer in c_generator)
                embed.add_field(name=cog.capitalize(), value=f"`{count}` lines.", inline=True)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))