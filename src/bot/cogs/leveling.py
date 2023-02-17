import asyncio
import typing as t
import datetime as dt
import random as r
import math
import re
import pytz

from discord.ext import commands
import discord

from src.bot.bot import MatrixineBot


class Leveling(commands.Cog):
    """Leveling commands and handles events"""

    def __init__(self, bot: MatrixineBot):
        self.bot = bot
        self.database = self.bot.MONGO_DB
        self.leveling = self.database["Leveling"]
        self.guilds = self.database["Guilds"]

    async def level_up_msg(self, msg: discord.Message):
        embed_settings = self.leveling.find_one({"_id": msg.guild.id})["embed_settings"]

        if not embed_settings:
            return
        if not embed_settings["title"] and not embed_settings["desc"]:
            return

        settings = [
            embed_settings["title"],
            embed_settings["desc"],
            embed_settings["footnote"],
            embed_settings["author"]
        ]

        member = msg.author

        keys = [
            "{user}",
            "{username}",
            "{server}",
            "{channel}",
        ]
        vals = [
            member.mention,
            member.display_name,
            member.guild.name,
            msg.channel.mention
        ]

        if self.guilds.find_one({"_id": msg.guild.id})["data"]["member"]["level_up_channel"]:
            level_up_channel = self.bot.get_channel(
                self.guilds.find_one({"_id": msg.guild.id})["data"]["member"]["level_up_channel"])
            keys.append("level_up_channel")
            vals.append(level_up_channel.mention)

        role_regex = r"\{\@[0-9]+\}"
        channel_regex = r"\{\#[0-9]+\}"
        for i in range(len(settings)):
            for match in re.findall(role_regex, settings[i]):
                role_id = match.replace("{", "").replace("}", "").replace("@", "")
                for g_role in msg.guild.roles:
                    if role_id in str(g_role.id):
                        settings[i] = settings[i].replace(match, g_role.mention)

            for match in re.findall(channel_regex, settings[i]):
                channel_id = match.replace("{", "").replace("}", "").replace("#", "")
                for g_channel in msg.guild.channels:
                    if channel_id in str(g_channel.id):
                        settings[i] = settings[i].replace(match, g_channel.mention)

            for j in range(len(keys)):
                settings[i] = settings[i].replace(keys[j], vals[j])

        embed = discord.Embed(
            title=settings[0],
            description=settings[1],
            timestamp=dt.datetime.utcnow(),
            color=embed_settings["color"]
        )

        if embed_settings["thumbnail"]:
            embed.set_thumbnail(url=embed_settings["thumbnail"])
        if embed_settings["image"]:
            embed.set_image(url=embed_settings["image"])
        if embed_settings["footnote"]:
            embed.set_footer(text=settings[2])
        if embed_settings["author"]:
            embed.set_author(name=settings[3])

        if self.guilds.find_one({"_id": msg.guild.id})["data"]["member"]["level_up_channel"]:
            level_up_channel = self.bot.get_channel(
                self.guilds.find_one({"_id": msg.guild.id})["data"]["member"]["level_up_channel"])
            await level_up_channel.send(embed=embed)

        else:
            ctx = await self.bot.get_context(message=msg)
            await ctx.send(embed=embed)

    async def process_xp(self, msg):
        user = msg.author
        guild = msg.guild
        result = self.leveling.find_one({"_id": guild.id})
        if not result:
            return

        if not self.guilds.find_one({"_id": guild.id})["data"]["member"]["leveling_enabled"]:
            return

        members = result["members"]
        try:
            members[str(user.id)]
        except KeyError:
            members[str(user.id)] = {
                "xp": 0,
                "level": 0,
                "lock_reason": None,
                "lock_time": dt.datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "times_locked": 0
            }
            self.leveling.update_one({"_id": guild.id}, {"$set": {"members": members}})

        if dt.datetime.strptime(result["members"][str(user.id)]["lock_time"], "%Y-%m-%dT%H:%M:%SZ") < dt.datetime.utcnow():
            await self.add_xp(msg, result)

        else:
            lock_time = result["members"][str(user.id)]["lock_time"]
            if lock_time < dt.datetime.now(pytz.utc):
                lock_reason = result["members"][str(user.id)]["lock_reason"]
                lock_reason = "NO LONGER LOCKED | " + lock_reason
                self.leveling.update_one({"_id": msg.guild.id}, {"$set": {f"member.{msg.author.id}.lock_reason": lock_reason}})

    async def add_xp(self, msg, result):
        if result["randomized"]:
            xp_to_add = result["multiplier"] * r.randint(1, 10)
        else:
            xp_to_add = result["multiplier"] * 5

        member = result["members"][str(msg.author.id)]

        xp = member["xp"] + xp_to_add
        current_lvl = member["level"]

        self.leveling.update_one({"_id": msg.guild.id}, {"$set": {f"members.{str(msg.author.id)}.xp": xp}})

        if (new_level := math.floor(int(xp // 42) ** 0.55)) > current_lvl:
            self.leveling.update_one({"_id": msg.guild.id},
                                     {"$set": {f"members.{str(msg.author.id)}.level": new_level}})
            await self.level_up_msg(msg)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        await self.process_xp(msg)

    @commands.command(name="SetLevelUpEmbedTitle", description="Sets the title of the embed sent when a user levels up")
    @commands.has_permissions(manage_guild=True)
    async def set_level_up_embed_title(self, ctx, *, title: t.Optional[str]):
        if not self.guilds.find_one({"_id": ctx.guild.id})["data"]["member"]["leveling_enabled"]:
            await ctx.send("Leveling is not enabled on this server!")
            return

        if not title:
            level_title = self.leveling.find_one({"_id": ctx.guild.id})["embed_settings"]["title"]
            if not level_title:
                await ctx.send("There is not level up embed title set for this server.")
            if level_title:
                await ctx.send(f"The current level up embed title set for this server is: \n{level_title}")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"embed_settings.title": title}})
        await ctx.send(f"Alright, I have set the level up embed title to `{title}`")

    @commands.command(name="SetLevelUpEmbedDescription", aliases=["SetLevelUpEmbedDesc"], description="Sets the description of the embed sent when a user levels up")
    @commands.has_permissions(manage_guild=True)
    async def set_level_up_embed_description(self, ctx, *, desc: t.Optional[str]):
        if not self.guilds.find_one({"_id": ctx.guild.id})["data"]["member"]["leveling_enabled"]:
            await ctx.send("Leveling is not enabled on this server!")
            return

        if not desc:
            level_desc = self.leveling.find_one({"_id": ctx.guild.id})["embed_settings"]["desc"]
            if not level_desc:
                await ctx.send("There is not level up embed desc set for this server.")
            if level_desc:
                await ctx.send(f"The current level up embed desc set for this server is: \n{level_desc}")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"embed_settings.desc": desc}})
        await ctx.send(f"Alright, I have set the level up embed desc to `{desc}`")

    @commands.command(name="SetLevelUpEmbedColor", description="Sets the color of the embed sent when a user levels up")
    @commands.has_permissions(manage_guild=True)
    async def set_level_up_embed_color(self, ctx, *, color: t.Optional[hex]):
        if not self.guilds.find_one({"_id": ctx.guild.id})["data"]["member"]["leveling_enabled"]:
            await ctx.send("Leveling is not enabled on this server!")
            return

        if not color:
            level_color = self.leveling.find_one({"_id": ctx.guild.id})["embed_settings"]["color"]
            if not level_color:
                await ctx.send("There is not level up embed color set for this server.")
            if level_color:
                await ctx.send(f"The current level up embed color set for this server is: `0x{level_color}`")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"embed_settings.color": color}})
        await ctx.send(f"Alright, I have set the level up embed color to `0x{color}`")

    @commands.command(name="SetLevelUpEmbedThumbnail", description="Sets the thumbnail of the embed sent when a user levels up (url's only)")
    @commands.has_permissions(manage_guild=True)
    async def set_level_up_embed_thumbnail(self, ctx, *, thumbnail_url: t.Optional[str]):
        if not self.guilds.find_one({"_id": ctx.guild.id})["data"]["member"]["leveling_enabled"]:
            await ctx.send("Leveling is not enabled on this server!")
            return

        if not thumbnail_url:
            level_thumbnail_url = self.leveling.find_one({"_id": ctx.guild.id})["embed_settings"]["thumbnail_url"]
            if not level_thumbnail_url:
                await ctx.send("There is not level up embed thumbnail_url set for this server.")
            if level_thumbnail_url:
                await ctx.send(
                    f"The current level up embed thumbnail_url set for this server is: \n{level_thumbnail_url}")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"embed_settings.thumbnail_url": thumbnail_url}})
        await ctx.send(f"Alright, I have set the level up embed thumbnail_url to `{thumbnail_url}`")

    @commands.command(name="SetLevelUpEmbedImage", description="Sets the image of the embed sent when a user levels up (url's only)")
    @commands.has_permissions(manage_guild=True)
    async def set_level_up_embed_image(self, ctx, *, image_url: t.Optional[str]):
        if not self.guilds.find_one({"_id": ctx.guild.id})["data"]["member"]["leveling_enabled"]:
            await ctx.send("Leveling is not enabled on this server!")
            return

        if not image_url:
            level_image_url = self.leveling.find_one({"_id": ctx.guild.id})["embed_settings"]["image_url"]
            if not level_image_url:
                await ctx.send("There is not level up embed image_url set for this server.")
            if level_image_url:
                await ctx.send(f"The current level up embed image_url set for this server is: \n{level_image_url}")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"embed_settings.image_url": image_url}})
        await ctx.send(f"Alright, I have set the level up embed image_url to `{image_url}`")

    @commands.command(name="SetLevelUpEmbedFooter", description="Sets the footer text of the embed sent when a user levels up")
    @commands.has_permissions(manage_guild=True)
    async def set_level_up_embed_footer(self, ctx, *, footer: t.Optional[str]):
        if not self.guilds.find_one({"_id": ctx.guild.id})["data"]["member"]["leveling_enabled"]:
            await ctx.send("Leveling is not enabled on this server!")
            return

        if not footer:
            level_footer = self.leveling.find_one({"_id": ctx.guild.id})["embed_settings"]["footer"]
            if not level_footer:
                await ctx.send("There is not level up embed footer set for this server.")
            if level_footer:
                await ctx.send(f"The current level up embed footer set for this server is: \n{level_footer}")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"embed_settings.footer": footer}})
        await ctx.send(f"Alright, I have set the level up embed footer to `{footer}`")

    @commands.command(name="SetLevelUpEmbedAuthor", description="Sets the author text of the embed sent when a user levels up")
    @commands.has_permissions(manage_guild=True)
    async def set_level_up_embed_author(self, ctx, *, author: t.Optional[str]):
        if not self.guilds.find_one({"_id": ctx.guild.id})["data"]["member"]["leveling_enabled"]:
            await ctx.send("Leveling is not enabled on this server!")
            return

        if not author:
            level_author = self.leveling.find_one({"_id": ctx.guild.id})["embed_settings"]["author"]
            if not level_author:
                await ctx.send("There is not level up embed author set for this server.")
            if level_author:
                await ctx.send(f"The current level up embed author set for this server is: \n{level_author}")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"embed_settings.author": author}})
        await ctx.send(f"Alright, I have set the level up embed author to `{author}`")

    @commands.command(name="level_info", aliases=["level_help"], description="Displays some of the information about the level up embed customizations")
    async def level_help_info(self, ctx):
        description = "`{user}`: Mentions a user. Will not work in the author, title, or footer field.\n" \
                      "`{username}`: Displays a username. Does work in all fields.\n" \
                      "`{server}`: Displays the server name. Does work in all fields.\n" \
                      "`{channel}`: Displays the channel where the level up occurred. Does not work in all fields.\n" \
                      "`{@role_id}`: Mentions a role. Only works with **ROLE ID**. Will not ping role. Does not work in all fields.\n"\
                      "`{#channel_id}`: Mentions a channel. Only works with **CHANNEL ID**. Does not work in all fields"

        embed = discord.Embed(
            title="Level Customization Information",
            description=description,
            color=self.bot.COLOR,
            timestamp=dt.datetime.utcnow()
        )

        embed.set_author(name=ctx.author.display_name)
        embed.set_footer(text="If there are any questions, ask Zettabite Pragmara#4031")

        await ctx.send(embed=embed)

    @commands.command(name="level", description="Displays a user's level")
    async def level_command(self, ctx, target: t.Optional[discord.Member]):
        if not target:
            target = ctx.author

        try:
            member = self.leveling.find_one({"_id": ctx.guild.id})["members"][str(target.id)]
        except KeyError:
            await ctx.send("That user is not in my database.")
            return

        xp = member["xp"]
        lvl = member["level"]
        isLocked = member["lock_time"] > dt.datetime.utcnow()
        if isLocked:
            unlockDate = dt.datetime.strftime(["lock_time"], "%Y-%m-%dT%H:%M:%SZ")
            currentDate = dt.datetime.strftime(dt.datetime.utcnow(), "%Y-%m-%dT%H:%M:%SZ")
            timeUntil = unlockDate - currentDate
            locked = f"User is xp locked for {timeUntil} days"
        else:
            locked = "User is not xp locked"

        embed = discord.Embed(
            title=f"{target.display_name} level",
            description=f"XP: {xp}\nLevel: {lvl}\n{locked}",
            color=self.bot.COLOR,
            timestamp=dt.datetime.utcnow()
        )

        embed.set_footer(text="Leveling system developed by Zettabite Pragmara#4031")
        embed.set_author(name=ctx.author.display_name)

        await ctx.send(embed=embed)

    @commands.command(name="xp_lock", description="Lets moderators prevent users from leveling up or gaining xp")
    @commands.has_permissions(manage_roles=True)
    async def lock_xp_command(self, ctx, target: t.Optional[discord.Member], duration: t.Optional[str], *, reason: t.Optional[str]):
        if not target:
            await ctx.send("You must specify a member to xp lock")
            return
        if target == ctx.author:
            await ctx.send("You cannot xp lock yourself")
            return
        reason = reason or "No reason"

        if duration:
            duration = duration.lower()
            timedelta = dt.timedelta()
            if "w" in duration:
                index = duration.find("w")
                timedelta += dt.timedelta(weeks=int(duration[:index]))
            if "d" in duration:
                start = duration.find("w") + 1
                end = duration.find("d")
                timedelta += dt.timedelta(days=int(duration[start:end]))
            if "h" in duration:
                start = duration.find("d") + 1
                end = duration.find("h")
                timedelta += dt.timedelta(hours=int(duration[start:end]))
            if "m" in duration:
                start = duration.find("h") + 1
                end = duration.find("m")
                timedelta += dt.timedelta(minutes=int(duration[start:end]))
            if "s" in duration:
                start = duration.find("m") + 1
                end = duration.find("s")
                timedelta += dt.timedelta(seconds=int(duration[start:end]))

            current_time = dt.datetime.now(pytz.utc)
            future_time = current_time + timedelta
            xp_lock_utc_timestamp = future_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {f"members.{target.id}.lock_time": xp_lock_utc_timestamp}})
            self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {f"members.{target.id}.lock_reason": f"{reason} | {duration}"}})
            times_locked = self.leveling.find_one({"_id": ctx.guild.id})["members"][str(target.id)]["times_locked"]
            self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {f"members.{target.id}.times_locked": times_locked + 1}})

            locked_times = ""
            if times_locked == 1:
                locked_times = "time before"
            else:
                locked_times = "times before"

            await ctx.send(f"Alright, I marked {target.display_name} as xp locked for {timedelta} for {reason}, and they have been locked {times_locked} {locked_times}")

    @commands.command(name="xp_unlock", description="Undoes the an XP lock")
    @commands.has_permissions(manage_roles=True)
    async def unlock_xp_command(self, ctx, target: t.Optional[discord.Member]):
        if not target:
            await ctx.send("You must specify a member to xp unlock")
            return
        if target == ctx.author:
            await ctx.send("You cannot xp unlock yourself")
            return

        lock_time = self.leveling.find_one({"_id": ctx.guild.id})["members"][str(target.id)]["lock_time"]
        now = dt.datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if lock_time < now:
            await ctx.send("That user is not xp locked!")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {f"members.{target.id}.lock_time": now}})
        lock_reason = self.leveling.find_one({"_id": ctx.guild.id})["members"][str(target.id)]["lock_reason"]
        lock_reason = "NO LONGER LOCKED | " + lock_reason
        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {f"members.{target.id}.lock_reason": lock_reason}})

        await ctx.send(f"I have unlocked {target.display_name}")

    @commands.command(name="remove_xp_lock", description="Subtracts from the number of times a user has been xp locked")
    @commands.has_permissions(manage_roles=True)
    async def remove_xp_lock_from_times_locked(self, ctx, count: t.Optional[int], target: t.Optional[discord.User]):
        count = count or 1
        target = target or ctx.author

        times_locked = self.leveling.find_one({"_id": ctx.guild.id})["members"][str(target.id)]["times_locked"]
        times_locked -= count
        if times_locked < 0:
            await ctx.send("The specified user already has never been xp locked")
            return

        lock_reason = f"The times_locked has been updated by {ctx.author.name}#{ctx.author.discriminator} at {dt.datetime.now(pytz.utc)}"
        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {f"members.{target.id}.times_locked": times_locked}})
        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {f"members.{target.id}.lock_reason": lock_reason}})

        await ctx.send(f"Alright, I removed an xp lock from {target.display_name}")

    @commands.command(name="xp_lock_reason", description="Sends the reason a user was XP locked")
    @commands.has_permissions(manage_roles=True)
    async def check_xp_lock_reason(self, ctx, target: t.Optional[discord.User]):
        target = target or ctx.author

        lock_reason = self.leveling.find_one({"_id": ctx.guild.id})["members"][str(target.id)]["lock_reason"]

        await ctx.send(f"{target.display_name}'s most recent lock reason:\n\t{lock_reason}")

    @commands.command(name="times_xp_locked", description="Sends the number of times a user was XP locked")
    async def check_times_xp_locked(self, ctx, target: t.Optional[discord.User]):
        target = target or ctx.author

        times_locked = self.leveling.find_one({"_id": ctx.guild.id})["members"][str(target.id)]["lock_reason"]

        await ctx.send(f"{target.display_name}'s most recent xp lock is number {times_locked}")

    @commands.command(name="reset_user_xp", description="Deletes a user from the database. Irreversible")
    @commands.has_permissions(administrator=True)
    async def reset_user_xp(self, ctx, target: t.Optional[discord.User]):
        target = target or ctx.author
        await ctx.send(f"Are you sure you want to delete {target.mention}'s level and xp information? This action is irreversible.")

        def check(m):
            return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=5.0)
        except asyncio.TimeoutError:
            return await ctx.send("The command timed out.")

        confirm = ["yes", "y"]
        if msg.content.lower() in confirm:
            self.leveling.update_one({"_id": ctx.guild.id}, {"$unset": {f"members.{target.id}": ""}})
            await ctx.send(f"Alright. I have deleted {target.mention} from the xp database.")
        else:
            await ctx.send("Alright. Canceling deletion.")

    @commands.command(name="randomize_xp")
    @commands.has_permissions(manage_guild=True)
    async def randomize_xp(self, ctx):
        result = self.leveling.find_one({"_id": ctx.guild.id})
        if not result:
            await ctx.send("I'm sorry but this server isn't in my database!")
            return

        set_state = not result["randomized"]

        if set_state:
            await ctx.send("Alright, I turned the xp randomization on")
        if not set_state:
            await ctx.send("Alright, I turned the xp randomization off")

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"randomized": set_state}})

    @commands.command(name="set_multiplier", aliases=["multiplier"])
    @commands.has_permissions(manage_guild=True)
    async def set_xp_multiplier(self, ctx, multiplier: t.Optional[float]):
        result = self.leveling.find_one({"_id": ctx.guild.id})
        if not result:
            await ctx.send("I'm sorry but this server isn't in my database!")
            return

        current_mul: float = result["multiplier"]
        if not multiplier:
            await ctx.send(f"The current xp multiplier for this server is {current_mul}")
            return

        self.leveling.update_one({"_id": ctx.guild.id}, {"$set": {"multiplier": multiplier}})
        await ctx.send(f"Alright! I changed the server's xp multiplier from {current_mul} to {multiplier}")


def setup(bot: MatrixineBot):
    bot.add_cog(Leveling(bot))
