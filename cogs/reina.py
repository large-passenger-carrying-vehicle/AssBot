import io

import aiohttp
from discord.ext import commands


class Reina:
    def __init__(self, bot):
        self.session = aiohttp.ClientSession(loop=bot.loop)

    def __unload(self):
        self.session.close()

    @commands.command()
    async def avatar(self, ctx, *, member: discord.Member = None):
        """Posts a member's avatar."""

        member = member or ctx.author
        avatar_url = member.avatar_url_as(static_format='png')

        async with self.session.get(avatar_url) as r:
            if r.status != 200:
                return await ctx.send('Failed to download avatar.')

            filetype = r.headers.get('Content-Type').split('/')[1]
            filename = f'{member.name}.{filetype}'
            await ctx.send(file=discord.File(io.BytesIO(await r.read()),
                           filename))


def setup(bot):
    bot.add_cog(Reina(bot))