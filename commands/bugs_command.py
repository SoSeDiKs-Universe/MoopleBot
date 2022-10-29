import re

import aiohttp
import discord

import mooplebot
from mooplebot import client as bot


webhook_url = mooplebot.get_env_value('BUGS_WEBHOOK')


async def process_bugs(message: discord.Message):
    channel = message.channel

    if channel.id != mooplebot.test_channel_id:
        return

    author: discord.User = message.author
    if author.id != 308293609566765058:
        await message.reply(content="No >:(")
        return

    guild = message.guild
    if guild is None:
        await message.reply(content="Wrong guild :(")
        return

    bugs_channel: discord.TextChannel = bot.get_channel(mooplebot.bugs_channel_id)
    if bugs_channel is None:
        await message.reply(content="#bugs channel not found :(")
        return

    bugs_message: discord.Message = await bugs_channel.fetch_message(919071446662262795)
    if bugs_message is None:
        await message.reply(content="#bugs message not found :(")
        return

    args = message.content.split(" ")
    bugs_embed = bugs_message.embeds[0]

    if len(args) == 1:
        buggies, buggies_notes = get_current_bugs(bugs_embed)
        response = get_bugs_response(buggies, buggies_notes, True)
        await show_bugs(channel, bugs_embed, response)
        return

    action = args[1]

    if action == "help":
        await show_help(message)
        return
    if action == "add":
        await add_bug(bugs_message, message, bugs_embed, args[2:])
        return
    if action == "del":
        await remove_bug(bugs_message, message, bugs_embed, args[2:])
        return
    if action == "note":
        await set_note(bugs_message, message, bugs_embed, args[2:])
        return
    if action == "noted":
        await del_note(bugs_message, message, bugs_embed, args[2:])
        return

    await message.reply(content="Unknown action o.0")


async def show_help(message):
    response = "**!bugs** - show numerated bugs"
    response += "\n**!bugs help** - show this message"
    response += "\n**!bugs add <type> <description>** - record new bug"
    response += "\n**!bugs del <type> <number>** - remove bug"
    response += "\n**!bugs note <type> <number> <note>** - set note for a bug"
    response += "\n**!bugs noted <type> <number>** - remove note for a bug"
    embed = discord.Embed(color=discord.Color.fuchsia(), title="Commands", description=response)
    embed.set_footer(text="Bug types: w, g, y, o, r")
    await message.reply(embed=embed)


async def show_bugs(channel, bugs_embed, response):
    embed = discord.Embed(color=bugs_embed.color, title=bugs_embed.title, description=response)
    await channel.send(embed=embed)


async def update_bugs(message, bugs_embed, response):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(url=webhook_url, session=session)
        embed = discord.Embed(color=bugs_embed.color, title=bugs_embed.title, description=response)
        await webhook.edit_message(message_id=message.id, embed=embed)


async def add_bug(bugs_message, message, bugs_embed, args):
    if len(args) < 2:
        await message.reply(content="Specify the bug type and describe it!")
        return

    bug_type = args[0]
    bug_type_full = get_circle(bug_type)

    if bug_type_full is None:
        await message.reply(content="Unknown bug type!")
        return

    description = " ".join(args[1:])
    added = bug_type_full + " " + description

    buggies, buggies_notes = get_current_bugs(bugs_embed)

    buggies[bug_type].insert(0, added)
    buggies_notes[bug_type].insert(0, None)

    embed = discord.Embed(title="Bug added!", description=added, color=discord.Color.green())
    await message.reply(embed=embed)

    response = get_bugs_response(buggies, buggies_notes)
    await update_bugs(bugs_message, bugs_embed, response)


async def set_note(bugs_message, message, bugs_embed, args):
    if len(args) < 3:
        await message.reply(content="Specify the bug type, number and a note!")
        return

    bug_type = args[0]
    bug_type_full = get_circle(bug_type)

    if bug_type_full is None:
        await message.reply(content="Unknown bug type!")
        return

    buggies, buggies_notes = get_current_bugs(bugs_embed)

    bug_index = int(args[1]) - 1
    bugs_size = len(buggies[bug_type])
    if bugs_size < bug_index:
        await message.reply(content="There are only " + str(bugs_size) + " bugs of type " + bug_type_full + "!")
        return

    note = " ".join(args[2:])

    while len(buggies_notes[bug_type]) <= bug_index:
        buggies_notes[bug_type].append(None)

    buggies_notes[bug_type][bug_index] = note

    description = buggies[bug_type][bug_index] + "\n" + format_note(note)

    embed = discord.Embed(title="Note added!", description=description, color=discord.Color.green())
    await message.reply(embed=embed)

    response = get_bugs_response(buggies, buggies_notes)
    await update_bugs(bugs_message, bugs_embed, response)


async def del_note(bugs_message, message, bugs_embed, args):
    if len(args) < 2:
        await message.reply(content="Specify the bug type and number!")
        return

    bug_type = args[0]
    bug_type_full = get_circle(bug_type)

    if bug_type_full is None:
        await message.reply(content="Unknown bug type!")
        return

    buggies, buggies_notes = get_current_bugs(bugs_embed)

    bug_index = int(args[1]) - 1
    bugs_size = len(buggies[bug_type])
    if bugs_size < bug_index:
        await message.reply(content="There are only " + str(bugs_size) + " bugs of type " + bug_type_full + "!")
        return

    if len(buggies_notes[bug_type]) <= bug_index or buggies_notes[bug_type][bug_index] is None:
        await message.reply(content="There is no note for that bug!")
        return

    removed = buggies_notes[bug_type][bug_index]
    description = buggies[bug_type][bug_index] + "\n" + format_note(removed)

    buggies_notes[bug_type][bug_index] = None

    embed = discord.Embed(title="Note removed!", description=description, color=discord.Color.red())
    await message.reply(embed=embed)

    response = get_bugs_response(buggies, buggies_notes)
    await update_bugs(bugs_message, bugs_embed, response)


async def remove_bug(bugs_message, message, bugs_embed, args):
    if len(args) < 2:
        await message.reply(content="Specify the bug type and number!")
        return

    bug_type = args[0]
    bug_type_full = get_circle(bug_type)

    if bug_type_full is None:
        await message.reply(content="Unknown bug type!")
        return

    remove_index = int(args[1]) - 1

    buggies, buggies_notes = get_current_bugs(bugs_embed)

    bugs_size = len(buggies[bug_type])
    if bugs_size <= remove_index:
        await message.reply(content="There are only " + str(bugs_size) + " bugs of type " + bug_type_full + "!")
        return

    removed = buggies[bug_type].pop(remove_index)
    if len(buggies_notes[bug_type]) > remove_index:
        del buggies_notes[bug_type][remove_index]

    embed = discord.Embed(title="Bug removed!", description=removed, color=discord.Color.red())
    await message.reply(embed=embed)

    response = get_bugs_response(buggies, buggies_notes)
    await update_bugs(bugs_message, bugs_embed, response)


def get_current_bugs(bugs_embed):
    description: str = bugs_embed.description
    bugs = description.split("\n")

    buggies = {'w': [], 'g': [], 'y': [], 'o': [], 'r': []}
    buggies_notes = {'w': [], 'g': [], 'y': [], 'o': [], 'r': []}
    previous_bug_type = None
    for index, bug in enumerate(bugs):
        if not re.match(r":.*_circle: .*", bug):
            if bug == "":
                continue
            bug_type = previous_bug_type
            if re.match(r".*- .*", bug):
                current_size = len(buggies[bug_type]) - 1
                while len(buggies_notes[bug_type]) < current_size:
                    buggies_notes[bug_type].append(None)
                buggies_notes[bug_type].append(bug.split("- ", 1)[1])
            continue
        bug_type = get_bug_type(bug)
        buggies[bug_type].append(bug)
        previous_bug_type = bug_type

    return buggies, buggies_notes


def get_bugs_response(buggies, buggies_notes, numerate=False):
    response = ""
    for bug_type, bugs in buggies.items():
        for index, bug in enumerate(bugs):
            if numerate:
                response += "**" + str(index + 1) + ":** "
            response += bug + "\n"
            if len(buggies_notes[bug_type]) <= index:
                continue
            note = buggies_notes[bug_type][index]
            if note is not None:
                response += format_note(note) + "\n"
        if len(buggies[bug_type]) != 0:
            response += "\n"

    if response == "":
        response = "There are no bugs! :o"
    else:
        response = response[:-1]

    return response


def format_note(note):
    nbs = "\u00A0"  # no-break space character
    return (nbs * 9) + "- " + note


def get_bug_type(bug):
    bug_type = bug.split(" ", 1)[0]
    bug_type = bug_type[1]
    return bug_type


def get_circle(bug_type):
    if bug_type == "g":
        color = "green"
    elif bug_type == "y":
        color = "yellow"
    elif bug_type == "o":
        color = "orange"
    elif bug_type == "r":
        color = "red"
    elif bug_type == "w":
        color = "white"
    else:
        return None
    return ":" + color + "_circle:"
