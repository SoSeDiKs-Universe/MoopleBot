import discord
from discord.ext import commands

from commands import ping_command, bugs_command, changelog_command


class CommandProcessor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        raw_message: str = message.content
        if raw_message.startswith("!ping"):
            await ping_command.process_ping(message)
        elif raw_message.startswith("!bugs"):
            await bugs_command.process_bugs(message)
        elif raw_message.startswith("!changelog"):
            await changelog_command.process_changelog(message)


async def setup(bot):
    await bot.add_cog(CommandProcessor(bot))
