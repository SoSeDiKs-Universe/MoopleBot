import asyncio
import sys
import os

from typing import List, Optional

import discord

from discord.ext import commands
from aiohttp import ClientSession

test_channel_id = 0
bugs_channel_id = 0
changelog_channel_id = 0


class MoopleBot(commands.Bot):
    def __init__(
            self,
            *args,
            initial_extensions: List[str],
            web_client: ClientSession,
            testing_guild_id: Optional[int] = None,
            intents: discord.Intents,
            **kwargs,
    ):
        super().__init__(*args, intents=intents, **kwargs)
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = initial_extensions

    async def setup_hook(self) -> None:
        for extension in self.initial_extensions:
            await self.load_extension(extension)

        if self.testing_guild_id is None:
            exit(1)
            return

        guild = discord.Object(self.testing_guild_id)
        # We'll copy in the global commands to test with:
        self.tree.copy_global_to(guild=guild)
        # followed by syncing to the testing guild.
        # await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f'Logged in as {self.user.name}#{self.user.discriminator}')
        print('------')


client: MoopleBot


async def main():
    mooplebot.test_channel_id = get_env_value('test_channel_id')
    mooplebot.bugs_channel_id = get_env_value('bugs_channel_id')
    mooplebot.changelog_channel_id = get_env_value('changelog_channel_id')
    async with ClientSession() as web_client:
        token = get_env_value('TOKEN')
        scope = int(get_env_value('GUILD_ID'))
        desc = "MoopleBot for SoSeDiK's Universe"
        exts = ["utils.command_processor"]

        intents = discord.Intents.all()
        bot = commands.Bot(command_prefix='!', description=desc, intents=intents)

        async with MoopleBot(bot, web_client=web_client, initial_extensions=exts,
                             testing_guild_id=scope, intents=intents) as bot:
            print("Starting the bot…")
            global client
            client = bot
            await bot.start(token)


def run_bot():
    asyncio.run(main())


def get_env_value(name):
    value = os.getenv(name)
    if value is None:
        sys.exit('Environment value missing: ' + name)
    return value
