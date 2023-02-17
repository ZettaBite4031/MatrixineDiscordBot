import typing as t
import datetime as dt
import re
import pytz

import discord
from discord.ext import commands
from discord.utils import get

from src.bot.bot import MatrixineBot


class Welcomer(commands.Cog):
    """Controls member and guild updates"""

    def __init__(self, bot: MatrixineBot):
        self.bot = bot
        self.database = self.bot.MONGO_DB
        self.guilds = self.database["Guilds"]
        self.leveling = self.database["Leveling"]

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        result = self.guilds.find_one({"_id": guild.id})
        if not result:
            data = {
                "join": {
                    "welcome_channel": None,
                    "welcome_message": None,
                    "leave_channel": None,
                    "leave_message": None,
                    "ban_message": None,
                    "auto_roles": []
                },
                "log": {
                    "deleted_message_channel": None,
                    "edited_message_channel": None,
                    "role_create_channel": None,
                    "role_edited_channel": None,
                    "member_update_channel": None,
                    "member_ban_channel": None,
                    "channel_event_channel": None,
                    "voice_event_channel": None
                },
                "member": {
                    "leveling_enabled": True,
                    "level_up_channel": None,
                    "no_level_roles": []
                }
            }
            self.guilds.insert_one({"_id": guild.id, "name": guild.name, "owner_id": guild.owner_id,
                                    "server_prefix": self.bot.PREFIX, "data": data})

            # Create table for Leveling database
            member = \
                {
                    str(guild.owner_id):
                    {
                        "xp": 0,
                        "level": 0,
                        "lock_reason": None,
                        "lock_time": dt.datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "times_locked": 0
                    }
                }
            embed = {
                    "title": None,
                    "desc": None,
                    "color": self.bot.COLOR,
                    "thumbnail": None,
                    "image": None,
                    "footnote": None,
                    "author": None
                }

            self.leveling.insert_one({"_id": guild.id,
                                      "name": guild.name,
                                      "multiplier": 1.0,
                                      "randomized": False,
                                      "members": member,
                                      "embed_settings": embed})

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        result = self.guilds.find_one({"_id": guild.id})
        if result:
            self.guilds.delete_one({"_id": guild.id})
            self.leveling.delete_one({"_id": guild.id})


    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        result = self.guilds.find_one({"_id": before.id})
        if result:
            self.guilds.update_one({"_id": before.id},
                                   {"$set": {"_id": after.id, "name": after.name, "owner_id": after.owner_id}})

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        result = self.guilds.find_one({"_id": member.guild.id})
        if not result:
            return
        welcome_message = str(result["data"]["join"]["welcome_message"])
        if not welcome_message:
            return
        if not result["data"]["join"]["welcome_channel"]:
            return
        welcome_channel = self.bot.get_channel(int(result["data"]["join"]["welcome_channel"]))
        user_keys = ["{user}", "{username}", "{server}", "{channel}"]
        mappings = [member.mention, member.display_name, member.guild.name, welcome_channel.mention]
        for i in range(len(user_keys)):
            welcome_message = welcome_message.replace(user_keys[i], mappings[i])

        await welcome_channel.send(welcome_message)

        roles = result['data']['join']['auto_roles']
        await member.edit(roles=(member.guild.get_role(id_) for id_ in roles))



    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return

        result = self.guilds.find_one({"_id": member.guild.id})
        if not result:
            return
        if not result["data"]["join"]["leave_channel"]:
            return

        leave_message = str(result["data"]["join"]["leave_message"])
        leave_channel = self.bot.get_channel(int(result["data"]["join"]["leave_channel"]))
        user_keys = ["{user}", "{username}", "{server}", "{channel}"]
        mappings = [member.mention, member.display_name, member.guild.name, leave_channel.mention]
        for i in range(len(user_keys)):
            leave_message = leave_message.replace(user_keys[i], mappings[i])

        await leave_channel.send(leave_message)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        pass

    @commands.command(name="set_welcome_channel", aliases=["welcome_channel"],
                      description="Sets the channel for the welcome message")
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        results = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})
        if not results:
            return await ctx.send("I couldn't find your server in my database!")

        self.bot.MONGO_DB["Guilds"].update_one({"_id": ctx.guild.id},
                                               {"$set": {"data.join.welcome_channel": int(channel.id)}})

        old_channel = results['data']['join']['welcome_channel']
        old_channel_name = "no channel"
        if old_channel:
            old_channel_name = self.bot.get_channel(old_channel).name
        await ctx.send(
            f"Alright! I changed the welcome channel from {old_channel_name} to {channel.mention}")

    @commands.command(name="set_welcome_message", aliases=["welcome_message"],
                      description="Sets the message for when a user joins the server!\nA welcome message must be specified!")
    @commands.has_permissions(manage_guild=True)
    async def set_welcome_message(self, ctx: commands.Context, *, message: str):
        if message.lower() == "none":
            message = None

        results = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})
        if not results:
            return await ctx.send("I could not find your server in my database!")

        self.bot.MONGO_DB["Guilds"].update_one({"_id": ctx.guild.id}, {"$set": {"data.join.welcome_message": message}})

        old_message = results['data']['join']['welcome_message']
        await ctx.send(
            f"Ok! I changed the leave message from {old_message if old_message else 'no message'} to {message}")

    @commands.command(name="set_leave_channel", aliases=["leave_channel"],
                      description="Sets the channel for the leave message")
    @commands.has_permissions(manage_guild=True)
    async def set_leave_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        results = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})
        if not results:
            return await ctx.send("I couldn't find your server in my database!")

        self.bot.MONGO_DB["Guilds"].update_one({"_id": ctx.guild.id},
                                               {"$set": {"data.join.leave_channel": int(channel.id)}})

        old_channel = results['data']['join']['leave_channel']
        old_channel_name = "no channel"
        if old_channel:
            old_channel_name = self.bot.get_channel(old_channel).name
        await ctx.send(
            f"Alright! I changed the leave channel from {old_channel_name} to {channel.mention}")

    @commands.command(name="set_leave_message", aliases=["leave_message"],
                      description="Sets the message for when a user leaves the server!\nA welcome message must be specified!")
    @commands.has_permissions(manage_guild=True)
    async def set_leave_message(self, ctx: commands.Context, *, message: str):
        if message.lower() == "none":
            message = None

        results = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})
        if not results:
            return await ctx.send("I could not find your server in my database!")

        self.bot.MONGO_DB["Guilds"].update_one({"_id": ctx.guild.id}, {"$set": {"data.join.leave_message": message}})

        old_message = results['data']['join']['welcome_message']
        await ctx.send(
            f"Ok! I changed the leave message from {old_message if old_message else 'no message'} to {message}")

    @commands.command(name="autoroles", description="Sets the autoroles for new members")
    @commands.has_permissions(manage_guild=True)
    async def set_autoroles(self, ctx: commands.Context, *, roles: t.Optional[discord.Role]):
        if not roles:
            roles = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})["data"]["join"]["auto_roles"]
            if not roles:
                return await ctx.send("You have no autoroles currently!")

            for i in range(len(roles)):
                roles[i] = get(ctx.guild.roles, id=int(roles[i])).mention
            return await ctx.send(f"You have {' '.join(roles)} set as autoroles on this server!")

        if roles == "none":
            self.bot.MONGO_DB["Guilds"].update_one({"_id": ctx.guild.id}, {"$set": {"data.join.auto_roles": []}})
            return await ctx.send("I removed all the autoroles!")

        result = self.bot.MONGO_DB["Guilds"].find_one({"_id": ctx.guild.id})
        if not result:
            return await ctx.send("I'm sorry! I couldn't find your server in my database!")

        roles = roles.split(" ")
        for i in range(len(roles)):
            roles[i] = int(roles[i].replace("<", "").replace(">", "").replace("@", "").replace("&", ""))

        self.bot.MONGO_DB["Guilds"].update_one({"_id": ctx.guild.id}, {"$set": {"data.join.auto_roles": roles}})
        await ctx.send(f"I added {len(roles)} roles to the autorole system!")



def setup(bot: MatrixineBot):
    bot.add_cog(Welcomer(bot))
