import datetime as dt
import pathlib as pl

import aiohttp
import discord
from pymongo import MongoClient
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.SekretDocuments.sekrets import Sekrets
OWNER_ID = [625382892419416074]
CO_OWNER_IDS = [901689854411300904]


class MatrixineBot(commands.Bot):
    def __init__(self):
        self.TOKEN = Sekrets.token
        self.COLOR = 0x1EACC4
        self.OWNER_ID = OWNER_ID
        self.OWNER_UN = "Zettabite Pragmara#4031"
        self.CO_OWNER_IDS = CO_OWNER_IDS
        self.VERSION = "a1.0.0"
        self.PREFIX = "M!"
        self.API_BASE = "https://discord.com/api/v9/"
        self.AIOHTTP_SESSION = aiohttp.ClientSession()
        self.APSCHEDULER = AsyncIOScheduler
        self.MONGO_CLUSTER = MongoClient(Sekrets.login)
        self.MONGO_DB = self.MONGO_CLUSTER["MatrixineDiscordBot"]
        self.stdout_id = 995733654783397888

        self._cogs = [p.stem for p in pl.Path(".").glob("./bot/cogs/*.py")]
        super().__init__(command_prefix=self.prefix,
                         owner_ids=self.OWNER_ID,
                         case_insensitive=True,
                         intents=discord.Intents.all())

    def setup(self):
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Beginning Setup...")


        for cog in self._cogs:
            self.load_extension(f"bot.cogs.{cog}")
            print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Loaded {cog} cog...")

        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Setup finished...")

    def run(self):
        self.setup()

        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def shutdown(self):
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Closing connection to Discord...")
        self.MONGO_CLUSTER.close()
        await super().close()

    async def close(self):
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Closing on keyboard interrupt...")
        await self.shutdown()

    async def on_connect(self):
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Bot connected to Discord API. Latency: {self.latency*1000:,.2f}ms.")

    async def on_resumed(self):
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Connection resumed. Latency: {self.latency*1000:,.2f}ms.")

    async def on_disconnect(self):
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Connection ended.")

    async def on_error(self, err, *args, **kwargs):
        raise

    async def on_command_error(self, ctx: commands.Context, exc):
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Encountered error while running '{ctx.command}' from {ctx.guild.name} ({ctx.guild.id}).")
        if isinstance(exc, commands.MissingRequiredArgument):
            print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Error: MissingRequiredArgument")
            await ctx.send("You're missing a required argument!")
            return

        raise getattr(exc, "original", exc)

    async def on_ready(self):
        await self.change_presence(activity=discord.Game("music | m!help"))
        self.BOT_INFO = await self.application_info()
        self.client_id = self.BOT_INFO.id
        self.stdout = self.get_channel(995733654783397888)
        await self.stdout.send(f"`{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}` | Bot ready! Latency: {self.latency*1000:,.2f}ms.")
        print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Bot ready... Latency: {self.latency*1000:,.2f}ms.")

    def prefix(self, bot, msg):
        result = self.MONGO_DB["Guilds"].find_one({"_id": msg.guild.id})
        if result:
            prefix = str(result["server_prefix"])
        else:
            prefix = self.PREFIX

        prefixes = commands.when_mentioned_or(prefix)(bot, msg)
        prefixes.append(prefix.lower())
        return prefixes

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)

        if ctx.command is not None:
            print(f"{dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} | Processing command, '{ctx.command}', from {ctx.guild.name} ({ctx.guild.id})")
            await self.invoke(ctx)

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)