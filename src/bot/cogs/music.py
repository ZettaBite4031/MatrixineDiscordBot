import asyncio, math, re, enum, os, base64
import datetime as dt
import typing as t
import random as r

import aiohttp
import discord
import wavelink
from discord.ext import commands

from src.SekretDocuments.sekrets import Sekrets

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
TIME_REGEX = r"([0-9]{1,2})[:ms](([0-9]{1,2})s?)?"
LYRICS_API = "https://some-random-api.ml/lyrics"
HZ_BANDS = (20, 40, 63, 100, 150, 250, 400, 450, 630, 1000, 1600, 2500, 4000, 10000, 16000)
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}


class AlreadyConnected(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class PlayerIsAlreadyPaused(commands.CommandError):
    pass


class PlayerIsAlreadyPlaying(commands.CommandError):
    pass


class NoMoreTracks(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class InvalidRepeatMode(commands.CommandError):
    pass


class VolumeTooLow(commands.CommandError):
    pass


class VolumeTooHigh(commands.CommandError):
    pass


class NoSearchQuery(commands.CommandError):
    pass


class MaxVolume(commands.CommandError):
    pass


class MinVolume(commands.CommandError):
    pass


class NoLyricsFound(commands.CommandError):
    pass


class InvalidEQPreset(commands.CommandError):
    pass


class NonexistentEQBand(commands.CommandError):
    pass


class EQGainOutOfBounds(commands.CommandError):
    pass


class InvalidTimeString(commands.CommandError):
    pass


class RepeatModes(enum.Enum):
    NONE = 0
    ONE = 1
    ALL = 2


class Queue:
    def __init__(self):
        self._queue = []
        self.pos = 0
        self.repeat_mode = RepeatModes.NONE

    def add(self, *args):
        self._queue.extend(args)

    @property
    def is_empty(self):
        return not self._queue

    @property
    def first_track(self):
        if not self._queue:
            raise QueueIsEmpty
        return self._queue[0]

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty

        if self.pos <= len(self._queue) - 1:
            return self._queue[self.pos]

    @property
    def upcoming_tracks(self):
        if not self.queue:
            raise QueueIsEmpty
        if self.pos <= len(self._queue):
            return self._queue[self.pos + 1]

    @property
    def next_track(self):
        if not self._queue:
            raise QueueIsEmpty
        return self._queue[self.pos + 1]

    @property
    def prev_track(self):
        if not self._queue:
            raise QueueIsEmpty
        if self.pos - 1 < 0:
            raise NoPreviousTracks
        return self._queue[self.pos - 1]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty
        return self._queue[:self.pos]

    @property
    def len(self):
        return len(self._queue)

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

        self.pos += 1

        if self.pos < 0:
            return None

        elif self.pos > len(self._queue) - 1:
            if self.repeat_mode == RepeatModes.ALL:
                self.pos = 0
            else:
                return None

        return self._queue[self.pos]

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty

        upcoming = self.upcoming_track
        r.shuffle(upcoming)
        self._queue = self._queue[:self.pos + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatModes.NONE
        elif mode == "one" or mode == 1:
            self.repeat_mode = RepeatModes.ONE
        elif mode == "all":
            self.repeat_mode = RepeatModes.ALL

    def empty(self):
        self._queue.clear()


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.eq_levels = [0.] * 15

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnected

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound

        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
            await ctx.send(f"Added {len(tracks.tracks)} tracks to the queue!")

        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            await ctx.send(f"Added {tracks[0].title} to the queue!")

        else:
            if (track := await self.choose_track(ctx, tracks)) is not None:
                self.queue.add(track)
                await ctx.send(f"Added {track.title} to the queue!")

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                    r.emoji in OPTIONS.keys()
                    and u == ctx.author
                    and r.message.id == msg.id
            )

        embed = discord.Embed(title="Choose a song",
                              description=(
                                  "\n".join(
                                      f"**{i + 1}.** {t.title} ({t.length / 60000:.0f}:{str(t.length % 60).zfill(2)})"
                                      for i, t in enumerate(tracks[:5])
                                  )
                              ),
                              color=self.bot.COLOR,
                              timestamp=dt.datetime.utcnow())
        embed.set_author(name="Query Results: ")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.first_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)

        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)


class Music(commands.Cog, wavelink.WavelinkMixin):
    """Handles music commands and functionality."""

    def __init__(self, bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        print(f'{dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} | Wavelink node, `{node.identifier}`, ready.')

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatModes.ONE:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands in DMs will not be processed.")
            return False
        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        nodes = {
            "MAIN": {
                "host": "127.0.0.1",
                "port": "9999",
                "rest_uri": "http://127.0.0.1:9999",
                "password": Sekrets.password,
                "identifier": "MAIN",
                "region": "us_east"
            }
        }

        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    @commands.command(name="connect", aliases=["join"],
                      description="""Connects the player to a channel. If one is not provided, it attempts to join the channel the user is current in""")
    async def connect_command(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.send(f'Connected to {channel.name}!')

    @connect_command.error
    async def connect_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnected):
            await ctx.send("I am already connected to another channel!")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("No voice channel with that name was found!")

    @commands.command(name="disconnect", aliases=["leave", "dc"],
                      description="""Disconnects the player from the voice channel it is currently in""")
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)
        if not player.queue.is_empty:
            player.queue.empty()
            await player.stop()
        await player.disconnect()
        await ctx.send("Disconnected!")

    @commands.command(name="play", aliases=["p", "resume", "unpause"],
                      description="""Plays the YouTube video queried by the executor of the command. Currently, only YouTube videos are supported.""")
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)

        if not player.is_connected:
            await player.connect(ctx)

        if query is None:
            if player.queue.is_empty:
                raise NoSearchQuery
            elif not player.is_paused:
                raise PlayerIsAlreadyPlaying
            elif player.is_paused:
                await player.set_pause(False)
                await ctx.send("Playback resumed!")

        else:
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"

            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @play_command.error
    async def play_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPlaying):
            await ctx.send("Playback is already running!")
        elif isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is empty!")
        elif isinstance(exc, NoSearchQuery):
            await ctx.send("You're missing a search query, and the queue is empty!")

    @commands.command(name="queue", aliases=["q"], description="""Lists the current queue of a player.""")
    async def queue_command(self, ctx, show: int = 10):
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Queue",
            colour=self.bot.COLOR,
            timestamp=dt.datetime.utcnow(),
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        if getattr(player.queue.current_track, "title"):
            track = player.queue.current_track
            value = f"**1.** {track.title} ({track.length / 60000:.0f}:{str(track.length % 60).zfill(2)})"
        elif not getattr(player.queue.current_track, "title"):
            value = "No tracks in queue."

        embed.add_field(name="Currently Playing", value=value, inline=False)
        embed.set_thumbnail(url=track.thumb)
        if upcoming := player.queue.upcoming_tracks:
            embed.add_field(
                name="Next up",
                value="\n".join(
                    f"**{i + 2}.** {t.title} ({t.length / 60000:.0f}:{str(t.length % 60).zfill(2)})" for i, t in
                    enumerate(upcoming[:5])),
                inline=False
            )

        msg = await ctx.send(embed=embed)

    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            embed = discord.Embed(
                title="Queue",
                color=self.bot.COLOR,
                timestamp=dt.datetime.utcnow()
            )
            embed.set_author(name="Query Results")
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            embed.add_field(name="There are no tracks in the queue.", value="** **", inline=False)
            await ctx.send(embed=embed)

    @commands.command(name="pause", description="Pauses playback")
    async def pause_command(self, ctx):
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        if player.is_paused:
            raise PlayerIsAlreadyPaused

        await player.set_pause(True)
        await ctx.send("Playback has been paused!")

    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("Playback is already paused!")

    @commands.command(name="stop", aliases=["clear", "empty"], description="""Stops the player and clears the queue""")
    async def stop_command(self, ctx):

        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.send("Playback stopped, and queue cleared!")

    @commands.command(name="skip", aliases=['s', 'next'],
                      description="""Skips the song it is playing and begins the upcoming song.""")
    async def skip_command(self, ctx):

        player = self.get_player(ctx)

        if not player.queue.upcoming_tracks:
            raise NoMoreTracks

        await ctx.send(f"Skipping {player.queue.current_track.title}, and playing {player.queue.next_track.title}!")
        await player.stop()

    @skip_command.error
    async def skip_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            ctx.send("The skip failed since the queue is empty!")
        elif isinstance(exc, NoMoreTracks):
            ctx.send("The queue is empty!")

    @commands.command(name="previous", aliases=['prev', 'backup'],
                      description="""Stops the current song and tracks back to the song that played before it.""")
    async def previous_command(self, ctx):

        player = self.get_player(ctx)

        if not player.queue.history:
            raise NoPreviousTracks
        if player.queue.is_empty:
            raise QueueIsEmpty

        await ctx.send(f"Reverting back to {player.queue.prev_track.title} from {player.queue.current_track.title}!")
        player.queue.position -= 2
        await player.stop()

    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            ctx.send("The command failed since the queue is empty!")
        elif isinstance(exc, NoPreviousTracks):
            ctx.send("The queue is empty!")

    @commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle_command(self, ctx):

        player = self.get_player(ctx)
        player.queue.shuffle()
        await ctx.send("Shuffled the queue!")

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue could not be shuffled since the queue is empty!")

    @commands.command(name="repeat", aliases=["loop"],
                      description="""Sets the repeat mode for the player. RepeatModes: None, One, All. The number 1 is valid as well.""")
    async def repeat_commands(self, ctx, mode: str):
        mode = mode.lower()
        if mode not in ("none", "1", "one", "all"):
            raise InvalidRepeatMode
        player = self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        await ctx.send(f"The repeat mode has been set to {mode}!")

    @commands.group(name="volume", invoke_without_command=True,
                    description="""Adjusts the volume of the bot. Cannot be set above 150 and cannot go below 0, and "up" and "down" can be taken as parameters to change the volume by 10%.""")
    async def volume_commands(self, ctx, volume: t.Optional[int]):

        player = self.get_player(ctx)
        if volume is None:
            return await ctx.send(f"The volume of the player is {player.volume}%!")

        if volume < 0:
            raise VolumeTooLow
        if volume > 150:
            raise VolumeTooLow

        await player.set_volume(volume)
        await ctx.send(f'Volume set to {volume}%!')

    @volume_commands.error
    async def volume_commands_error(self, ctx, exc):
        if isinstance(exc, VolumeTooLow):
            ctx.send("The volume can't be set below 0%!")
        elif isinstance(exc, VolumeTooHigh):
            ctx.send("The volume can't be set higher than 150%!")

    @volume_commands.command(name="up")
    async def volume_up_command(self, ctx):
        player = self.get_player(ctx)

        if player.volume == 150:
            raise MaxVolume

        await player.set_volume(value := min(player.volume + 10, 150))
        await ctx.send(f"Volume turned up to {value}%!")

    @volume_up_command.error
    async def volume_up_error(self, ctx, exc):
        if isinstance(exc, MaxVolume):
            await ctx.send("You can't turn up the volume anymore!")

    @volume_commands.command(name="down")
    async def volume_down_command(self, ctx):
        player = self.get_player(ctx)

        if player.volume == 0:
            raise MinVolume

        await player.set_volume(value := max(player.volume - 10, 150))
        await ctx.send(f"Volume turned down to {value}%!")

    @volume_down_command.error
    async def volume_down_error(self, ctx, exc):
        if isinstance(exc, MinVolume):
            await ctx.send("You can't turn the volume down any further!")

    @commands.command(name="lyrics", aliases=["lyric"],
                      description="""Can be used to obtain the lyrics of a song using the title of what is playing in the player. Does not have everything.""")
    async def lyrics_command(self, ctx, name: t.Optional[str]):

        player = self.get_player(ctx)
        name = name or player.queue.current_track.title
        async with ctx.typing():
            async with aiohttp.request("GET", LYRICS_API + "?title=" + name, headers={}) as r:
                if not 200 <= r.status <= 299:
                    raise NoLyricsFound

                data = await r.json()
                if len(data["lyrics"]) > 2000:
                    return await ctx.send(f"The lyrics were too long!\nHere's a link: <{data['links']['genius']}>")

                embed = discord.Embed(
                    title=data['title'] + " Lyrics",
                    description=data['lyrics'],
                    color=self.bot.COLOR,
                    timestamp=dt.datetime.utcnow()
                )
                embed.set_thumbnail(url=data['thumbnail']['genius'])
                embed.set_author(name=data['author'])
                await ctx.send(embed=embed)

    @lyrics_command.error
    async def lyrics_command_error(self, ctx, exc):
        if isinstance(exc, NoLyricsFound):
            await ctx.send(f"I'm sorry but the API, {LYRICS_API}, did not have an entree for that song!")

    @commands.command(name="equaliser", aliases=['eq'],
                      description="""Sets basic equalisers for the bot that change the audio. Flat is normal, and there's Boost, Metal, and Piano as the other three presets.""")
    async def eq_commands(self, ctx, preset: str):

        player = self.get_player(ctx)

        eq = getattr(wavelink.eqs.Equalizer, preset, None)
        if not eq:
            raise InvalidEQPreset

        await player.set_eq(eq())
        await ctx.send(f"Equaliser adjusted to the {preset} preset!")

    @eq_commands.error
    async def eq_command_error(self, ctx, exc):
        if isinstance(exc, InvalidEQPreset):
            await ctx.send("The equaliser preset must be either 'flat', 'boost', 'metal', or 'piano'!")

    eq_desc = """The advanced equaliser command allows users to alter the gain between +/-10dB on 15 separate Hz Bands: 20, 40, 63, 100, 150, 250, 400, 450, 630, 1000, 1600, 2500, 4000, 10000, 16000."""

    @commands.command(name="advanced-equaliser", aliases=['adveq', 'aeq', 'adeq', 'advanced-eq'], description=eq_desc)
    async def advanced_equaliser_command(self, ctx, band: int, gain: float):

        player = self.get_player(ctx)

        if not 1 <= band <= 15 and band not in HZ_BANDS:
            raise NonexistentEQBand

        if band > 15:
            band = HZ_BANDS.index(band) + 1

        if abs(gain) > 10:
            raise EQGainOutOfBounds

        player.eq_levels[band - 1] = gain / 10
        eq = wavelink.eqs.Equalizer(levels=[(i, gain) for i, gain in enumerate(player.eq_levels)])
        await player.set_eq(eq)
        await ctx.send(f"Equaliser adjusted with a band of {band} and gain of {gain}!")

    @advanced_equaliser_command.error
    async def advanced_equaliser_error(self, ctx, exc):
        if isinstance(exc, NonexistentEQBand):
            await ctx.send(
                "This is a 15 band equaliser -- the band number should be between 1 and 15, or one of the following"
                "frequencies: " + ", ".join(str(b) for b in HZ_BANDS) + "!"
            )
        elif isinstance(exc, EQGainOutOfBounds):
            await ctx.send("The EQ gain for any band should be between 10 dB and -10 dB!")

    @commands.command(name="playing", aliases=['nowplaying', 'np'],
                      description="""Lists the audio currently playing and the position the player is at.""")
    async def now_playing_command(self, ctx):

        player = self.get_player(ctx)

        if not player.is_playing and not player.queue.is_empty:
            raise PlayerIsAlreadyPaused
        elif not player.is_playing and player.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Now Playing",
            color=self.bot.COLOR,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Playback Information")
        embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
        embed.add_field(name="Track title", value=player.queue.current_track.title, inline=False)
        embed.add_field(name="Channel", value=player.queue.current_track.author, inline=False)

        pos = divmod(player.position, 60000)
        length = divmod(player.queue.current_track.length, 60000)
        embed.add_field(
            name="Position",
            value=f"{int(pos[0])}:{round(pos[1] / 1000):02}/{int(length[0])}:{round(length[1] / 1000):02}",
            inline=False
        )

        await ctx.send(embed=embed)

    @now_playing_command.error
    async def now_playing_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("There is no track currently playing!")
        elif isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is empty and there is nothing playing!")

    @commands.command(name="skipto", aliases=["st", "s2", "playindex", "pi", "pindex"],
                      description="""Allows the user to skip more than one song in the queue without spamming the skip command""")
    async def skipto_command(self, ctx, index: int):

        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty
        if not 0 <= index <= player.queue.len:
            raise NoMoreTracks

        player.queue.position = index - 2
        await player.stop()
        await ctx.send(f"Skipping to track in position {index}!")

    @skip_command.error
    async def skipto_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is empty!")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("There are no more tracks in the queue!")

    @commands.command(name='restart', description="""Restarts the song from 00:00.""")
    async def restart_song_command(self, ctx):

        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        await player.seek(0)
        await ctx.send("Track restarted!")

    @restart_song_command.error
    async def restart_song_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is empty!")

    seek_description = """The seek command will place the position of the player at a time in the song given. Format of the time must be <minutes>m<seconds>s. For example, 3m13s will skip to 3 minutes and 13 seconds in, but a user can leave off the minutes to skip only seconds. For example: 41s."""

    @commands.command(name="seek", description=seek_description)
    async def seek_time_command(self, ctx, pos: str):

        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty
        if not (match := re.match(TIME_REGEX, pos)):
            raise InvalidTimeString

        if match.group(3):
            secs = (int(match.group(1)) * 60) + (int(match.group(3)))
            minutes = math.floor(secs / 60)
            seconds = secs % 60
            if minutes == 1 and seconds == 1:
                time = f"{minutes:.0f} minute and {seconds} second"
            elif minutes == 1 and not seconds == 1:
                time = f"{minutes:.0f} minute and {seconds} seconds"
            elif not minutes == 1 and seconds == 1:
                time = f"{minutes:.0f} minutes and {seconds} second"
            elif not minutes == 1 and not seconds == 1:
                time = f"{minutes:.0f} minutes and {seconds} seconds"
        else:
            secs = int(match.group(1))
            if not secs == 1:
                time = f"{secs} seconds"
            elif secs == 1:
                time = f"{secs} second"

        await player.seek(secs * 1000)
        await ctx.send(f"The playback has been navigated to {time}!")


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
