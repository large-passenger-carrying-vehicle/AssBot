import discord
from discord.ext import commands

import configparser
import asyncio
import youtube_dl
import functools
from concurrent.futures import ThreadPoolExecutor
import os

from cogs.error import ResponseStatusError
from utils import checks


async def myst_fetch(session, url: str, timeout: float = None, raise_over: int = 300, body: str = 'json'):
    async with session.get(url, timeout=timeout) as resp:
        if resp.status >= raise_over:
            raise ResponseStatusError(resp.status, resp.reason, url)
        cont = getattr(resp, body)
        return await cont()


class CuteListeners:
    pass


class MystRandomThings:
    def __init__(self, bot):
        self.bot = bot
        self.threadex = ThreadPoolExecutor(max_workers=2)

    @commands.group(name='decrypt', invoke_without_command=True)
    async def decrypters(self, ctx):
        pass

    @decrypters.command(name='binary', aliases=['b1nary', '0101', '01'])
    async def binary_decrpyt(self, ctx, *, inp: str):
        """Decrypt binary"""
        inp = inp.replace(' ', '')

        try:
            out = ''.join(chr(int(inp[i * 8:i * 8 + 8], 2)) for i in range(len(inp) // 8))
        except:
            return await ctx.send('**This is not binary!**')

        return await ctx.send(out)

    @commands.command(name='getsong', aliases=['song_download', 'downloadsong'])
    async def download_ytaudio(self, ctx, *, url: str):
        """Downloads a song from YouTube and sends it back to the user."""
        # todo Filter non YouTube stuff.
        # todo Better error handling on large files.

        if '&list=' in url:
            return await ctx.send('Please provide a valid YouTube link. Playlists are not accepted.')

        opts = {
            'format': 'bestaudio/best',
            'max_filesize': '25mb',
            'outtmpl': f'%(extractor)s_%(title)s%(id)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
        }

        msg = await ctx.send('Attempting to retrieve your song.')

        ytdl = youtube_dl.YoutubeDL(opts)
        dl = functools.partial(ytdl.extract_info, url=url, download=True)
        data = await self.bot.loop.run_in_executor(self.threadex, dl)

        try:
            filename = ytdl.prepare_filename(data['entries'][0])
        except (KeyError, ValueError, TypeError):
            pass

        filename = ytdl.prepare_filename(data)

        try:
            await ctx.send(content=None, file=discord.File(filename))
        except:
            await ctx.send(f'There was an error processing your song. Perhaps the file was too large.')

        try:
            os.remove(filename)
        except Exception as e:
            print(e)
        
        try:
            await msg.delete()
        except:
            pass

    @commands.command(name='cfgadd')
    @checks.has_contrib_role()
    async def add_config(self, ctx, section: str, option: str, value: str):
        """Add a config to config.ini"""
        config = configparser.ConfigParser()
        config.read('config.ini')

        try:
            config.add_section(section=section)
        except configparser.DuplicateSectionError:
            try:
                await ctx.message.delete()
            except:
                pass
            return await ctx.send('That section already exists.')

        config.set(section=section, option=option, value=value)

        try:
            await ctx.message.delete()
        except:
            return await ctx.send('I have add your entry to the Config. It is a good idea to delete your message.')

        await ctx.send('I have add your entry to the Config.')


class MystWeather:
    def __init__(self, bot):
        self.bot = bot
        key = configparser.ConfigParser()
        key.read('config.ini')
        self._key = key.get("WEATHER", "_key")

    @commands.command(name='weather', aliases=['w', 'conditions'])
    async def get_weather(self, ctx, *, location: str = None):
        """Check the weather in a location"""
        if location is None:
            return await ctx.send('Please provide a location to get Weather Information for.')

        base = f'http://api.apixu.com/v1/current.json?key={self._key}&q={location}'

        try:
            data = await myst_fetch(ctx.session, base, 15, raise_over=300, body='json')
        except asyncio.TimeoutError:
            return await ctx.send('Our Weather API seems to be experiencing difficulties. Please try again later.')
        except ResponseStatusError:
            return await ctx.send('There was an error with your request. Please try again with a different location.')

        location = data['location']
        locmsg = f'{location["name"]}, {location["region"]} {location["country"].upper()}'
        current = data['current']

        colour = 0xfeff3f if current['is_day'] != 0 else 0x37074b
        embed = discord.Embed(title=f'Weather for {locmsg}',
                              description=f'*{current["condition"]["text"]}*',
                              colour=colour)
        embed.set_thumbnail(url=f'http:{current["condition"]["icon"]}')
        embed.add_field(name='Temperature', value=f'{current["temp_c"]}°C | {current["temp_f"]}°F')
        embed.add_field(name='Feels Like', value=f'{current["feelslike_c"]}°C | {current["feelslike_f"]}°F')
        embed.add_field(name='Precipitation', value=f'{current["precip_mm"]} mm')
        embed.add_field(name='Humidity', value=f'{current["humidity"]}%')
        embed.add_field(name='Windspeed', value=f'{current["wind_kph"]} kph | {current["wind_mph"]} mph')
        embed.add_field(name='Wind Direction', value=current['wind_dir'])

        await ctx.send(content=None, embed=embed)


class MystMain:
    pass


class MystHandlers:
    pass


def setup(bot):
    bot.add_cog(MystRandomThings(bot))
    bot.add_cog(MystWeather(bot))
