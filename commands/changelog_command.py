import aiohttp
import discord

import mooplebot


webhook_url = mooplebot.get_env_value("CHANGELOG_WEBHOOK")
# webhook_url = mooplebot.get_env_value("TEST_WEBHOOK")


async def process_changelog(message: discord.Message):
    channel = message.channel

    if channel.id != mooplebot.test_channel_id:
        return

    author: discord.User = message.author
    if author.id != 308293609566765058:
        await message.reply(content="No >:(")
        return

    content = message.content.split("\n")[1:]
    picture = message.attachments[0] if len(message.attachments) > 0 else None
    emoji = ":heart:"
    logs = {}
    for line in content:
        # emoji
        if line.startswith("$"):
            emoji = line.strip()[2:]
            continue
        # header
        if line.startswith("#"):
            line = line.strip()[2:]
            logs[line] = []
            continue
        # point
        if line.startswith("-"):
            line = "\n> • " + line.strip()[2:]
            logs[get_nth_key(logs, len(logs) - 1)].append(line)
            continue
        # multi-lined point
        line = "\n> " + line
        points = logs[get_nth_key(logs, len(logs) - 1)]
        points[len(points) - 1] += line

    description = ""
    for header, points in logs.items():
        description += "**" + header + "**\n"
        for point in points:
            description += point
        description += "\n\n"

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(url=webhook_url, session=session)
        embed = discord.Embed(color=16758328, description=description)
        embed.set_footer(text="sosedik.com")
        if picture is not None:
            embed.set_image(url=picture.url)
        sent_message = await webhook.send(embed=embed, username="Ура, обнова!", wait=True)
        if sent_message is discord.WebhookMessage:
            await sent_message.add_reaction(emoji)


def get_nth_key(dictionary, n=0):
    if n < 0:
        n += len(dictionary)
    for i, key in enumerate(dictionary.keys()):
        if i == n:
            return key
    raise IndexError("dictionary index out of range")
