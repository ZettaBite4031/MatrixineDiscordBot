import datetime as dt
import typing as t

import discord
from discord.ext import commands

true = True

class Mod(commands.Cog):
    """Handles moderation commands and functionality."""
    def __init__(self, bot):
        self.bot = bot

    async def timeout_user(self, userID, guildID, time):
        headers = {"Authorization": f"Bot {self.bot.http.token}"}
        url = f"https://discord.com/api/v9/guilds/{guildID}/members/{userID}"
        timeout = (dt.datetime.utcnow() + dt.timedelta(seconds=time)).isoformat()
        json = {'communication_disabled_until': timeout}
        async with self.bot.session.patch(url, json=json, headers=headers) as session:
            if session.status in range(200, 299):
                return True
            return False

    @commands.command(name="ban", description="Bans the mentioned users. Can accept multiple users at once.")
    @commands.has_permissions(ban_members=true)
    async def ban_user_command(self, ctx, targets: commands.Greedy[discord.User], *, reason: t.Optional[str] = "No reason"):
        if not len(targets):
            await ctx.send("You're missing a required argument! -> target(s) <-")
            return

        banned = ""
        colorAvg = ctx.author.id
        for target in targets:
            guild = ctx.guild
            member = guild.get_member(discord.User.id)
            banned += f"{target.name}#{target.discriminator}\n"
            if member is not None:
                if ctx.guild.me.top_role.position > target.top_role.position and not target.guild_permissions.administrator:
                    await target.ban(reason=reason)

                elif ctx.guild.me.top_role.position < target.top_role.position or target.guild_permissions.administrator:
                    await ctx.send(f"I can't ban {target.name}")

            elif member is None:
                await guild.ban(target, reason=reason)

            colorAvg += (ctx.author.id + target.id) / 2

        if len(targets) == 1:
            msg = f"1 member banned for {reason.lower()}"
        else:
            msg = f"{len(targets)} members banned {reason.lower()}"

        embed = discord.Embed(
            title=msg,
            description=f"{ctx.author.mention} had {msg}:\n{banned}",
            color=discord.Color.random(seed=colorAvg),
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}",
                         icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Imagine being a loser.")
        await ctx.send(embed=embed)

    @commands.command(name="unban", description="Unbans the mentioned users. Can accept multiple users at once.")
    @commands.has_permissions(ban_members=true)
    async def unban_member_command(self, ctx, targets: commands.Greedy[discord.User], *, reason: t.Optional[str] = "No reason"):
        if not len(targets):
            await ctx.send("Your missing a required argument! -> target(s) <-")
            return

        colorAvg = ctx.author.id
        unbanned = ""
        for target in targets:
            await ctx.guild.unban(target, reason=reason)
            unbanned += f"{target.name}#{target.discriminator}\n"

        if len(targets) == 1:
            msg = f"1 member unbanned for {reason.lower()}"
        else:
            msg = f"{len(targets)} members unbanned for {reason.lower()}"

        embed = discord.Embed(
            title=msg,
            description=f"{ctx.author.mention} had {msg}:\n{unbanned}",
            color=discord.Color.random(seed=colorAvg),
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}",
                         icon_url=ctx.author.avatar_url)
        embed.set_footer(text="No longer losers.")
        await ctx.send(embed=embed)

    @commands.command(name="purge", description="Deletes the amount of messages specified up to 2 weeks.")
    @commands.has_permissions(manage_messages=true)
    async def purge_messages_command(self, ctx, count: int, targets: commands.Greedy[discord.User]):
        def _check(msg):
            return not len(targets) or msg.author in targets

        if count < 0:
            ctx.send("Please use a positive, non-zero number :1")
            return

        with ctx.channel.typing():
            deleted = await ctx.channel.purge(limit=count, after=dt.datetime.utcnow() - dt.timedelta(days=14),
                                              check=_check)
            await ctx.send(f"I deleted {len(deleted)} messages!")

    @commands.command(name="mute", aliases=["timeout"], description="Times out the mentioned users. Can accept multiple users at once.")
    @commands.has_permissions(manage_roles=true)
    async def mute_member_command(self, ctx, targets: commands.Greedy[discord.User],
                                 time: t.Optional[str], *,
                                 reason: t.Optional[str] = "No reason"):
        if not len(targets):
            await ctx.send("You must specify a target member!")
            return

        if not time:
            await ctx.send("You must specify a maximum time!")
            return

        guild = ctx.guild
        time = time.lower()
        timeNo = int(time.replace("s", "").replace("m", "").replace("h", "").replace("d", "").replace("w", ""))
        timeMul = time[-1]
        display = ""
        muteTime = 0
        if timeNo >= 1:
            if "s" in timeMul:
                muteTime = timeNo # No conversion needed (seconds to seconds)
                display = "second"
            elif "m" in timeMul:
                muteTime = timeNo * 60  # Minutes to seconds
                display = "minute"
            elif "h" in timeMul:
                muteTime = timeNo * 3600 # Hours to seconds
                display = "hour"
            elif "d" in timeMul:
                muteTime = timeNo * 24 * 3600 # Days to hours to seconds
                display = "day"
            elif "w" in timeMul:
                muteTime = timeNo * 168 * 3600 # Weeks to hours to seconds
                display = "week"
            if timeNo > 1:
                display += "s"
        elif timeNo < 0:
            await ctx.send("Mute length must be a whole number greater than or equal to 1.")
            return

        muted = ""
        for target in targets:
            handshake = await self.timeout_user(target.id, guild.id, muteTime)
            if handshake:
                muted += f"{target.name}#{target.discriminator}\n"
                if len(targets) == 1:
                    msg = f"1 member muted for {reason.lower()}"
                else:
                    msg = f"{len(targets)} members muted for {reason.lower()}"

                embed = discord.Embed(
                    title=msg,
                    description=f"{ctx.author.mention} had {msg}:\n{muted}",
                    color=self.bot.COLOR,
                    timestamp=dt.datetime.utcnow()
                )
                embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}",
                                 icon_url=ctx.author.avatar_url)
                embed.set_footer(text="Imagine being losers.")
                return await ctx.send(embed=embed)

            await ctx.send(f"I could not mute {target.mention}")

    @commands.command(name="unmute", description="Removes the time out from the mentioned users. Can accept multiple users at once.")
    @commands.has_permissions(manage_roles=true)
    async def unmute_member_command(self, ctx, targets: commands.Greedy[discord.User], *,
                                    reason: t.Optional[str] = "No reason"):
        if not len(targets):
            await ctx.send("You must specify a target member!")
            return

        unmuted = ""
        for target in targets:
            handshake = await self.timeout_user(target.id, ctx.guild.id, 0)
            if handshake:
                unmuted += f"{target.name}#{target.discriminator}\n"
                if len(targets) == 1:
                    msg = f"1 member unmuted for {reason.lower()}"
                else:
                    msg = f"{len(targets)} members unmuted for {reason.lower()}"

                embed = discord.Embed(
                    title=msg,
                    description=f"{ctx.author.mention} had {msg}:\n{unmuted}",
                    color=self.bot.COLOR,
                    timestamp=dt.datetime.utcnow()
                )
                embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}",
                                 icon_url=ctx.author.avatar_url)
                embed.set_footer(text="No longer losers.")
                return await ctx.send(embed=embed)

            await ctx.send(f"I could not unmute {target.mention}")

    @commands.command(name="change_prefix", aliases=["prefix"], description="Changes the guild prefix of the bot")
    @commands.has_permissions(manage_guild=true)
    async def change_guild_prefix(self, ctx: commands.Context, prefix: str):
        result = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})
        if not result:
            return await ctx.send("There was an issue and I could not find your server in my database!")

        self.bot.MONGO_DB["Guilds"].update_one({"_id": ctx.guild.id}, {"$set": {"server_prefix": prefix}})
        await ctx.send(f"Alright! I changed the server prefix from {result['server_prefix']} to {prefix}!")


def setup(bot):
    bot.add_cog(Mod(bot))