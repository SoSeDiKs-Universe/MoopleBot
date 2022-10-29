import requests
import discord


async def process_ping(message: discord.Message):
    embed = discord.Embed(color=3158326, title="Up and running! :sweat_drops:")
    image_url = requests.get(url="https://picsum.photos/600").url
    embed.set_image(url=image_url)
    await message.channel.send(embed=embed)
