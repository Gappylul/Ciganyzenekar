import discord
import os
import yt_dlp
import logging
from dotenv import load_dotenv
from collections import deque
import asyncio

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Setting up logging
logging.basicConfig(level=logging.INFO)

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
}

ffmpeg_opts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
    'executable': 'C:/Users/Balázs/Downloads/ffmpeg-2024-06-21-git-d45e20c37b-essentials_build/bin/ffmpeg.exe'  # Add hozzá ezt a sort
}

# Initialize deque for the playlist
playlist = deque()
current_song_index = -1  # Start with no song playing

async def join_channel(message):
    if message.author.voice:
        channel = message.author.voice.channel
        await channel.connect()
    else:
        await message.channel.send("Még nem vagy a hangcsatornában.")

async def leave_channel(message):
    if message.guild.voice_client:
        await message.guild.voice_client.disconnect()

async def play_next_song(message):
    global current_song_index
    voice_client = message.guild.voice_client
    if current_song_index < len(playlist) - 1:
        current_song_index += 1
        song = playlist[current_song_index]
        voice_client.play(discord.FFmpegPCMAudio(song['url'], **ffmpeg_opts),
                          after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(message), client.loop))
        await message.channel.send(f'Speciálba: {song["title"]}')
    else:
        current_song_index = -1
        await message.channel.send("A lejátszási lista üres.")

async def play_song(message, song_query, artist_query=None):
    query = f"{song_query} {artist_query}" if artist_query else song_query

    voice_client = message.guild.voice_client
    if not voice_client:
        await join_channel(message)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
        if 'entries' in search_results and len(search_results['entries']) > 0:
            song_info = search_results['entries'][0]
            playlist.append({'url': song_info['url'], 'title': song_info['title']})
            await message.channel.send(f'Hozzáadva a lejátszási listához: {song_info["title"]}')
            if current_song_index == -1:
                await play_next_song(message)
        else:
            await message.channel.send("Nem találtam ilyet :(")

async def skip_song(message):
    if message.guild.voice_client and message.guild.voice_client.is_playing():
        message.guild.voice_client.stop()

async def display_queue(message):
    if playlist:
        queue_message = "Jelenlegi lejátszási lista:\n"
        for idx, song in enumerate(playlist):
            queue_message += f"{idx + 1}. {song['title']}\n"
    else:
        queue_message = "A lejátszási lista üres."
    await message.channel.send(queue_message)

async def display_help(message):
    help_message = """
Commands available:
- !huzdideasegged: Join the voice channel of the user who sent the command.
- !takarodc: Leave the current voice channel.
- !ropjad [song_name] [artist_name (optional)]: Add a song to the queue and play it if nothing is playing.
- !tovabb: Skip to the next song in the queue.
- !sor: Display the current song queue.
- !buhbye: Clear the entire playlist.
- !help: Display this help message.
"""
    await message.channel.send(help_message)

async def buh_bye(message):
    global current_song_index
    playlist.clear()
    current_song_index = -1
    await message.channel.send("A lejátszási lista törölve.")

@client.event
async def on_ready():
    print(f'Bejelentkezve {client.user}')

@client.event
async def on_message(message):
    print("Received message:", message.content)  # Debug print statement
    if message.author == client.user:
        return

    if message.content.startswith('!huzdideasegged'):
        await join_channel(message)

    elif message.content.startswith('!takarodc'):
        await leave_channel(message)

    elif message.content.startswith('!ropjad'):
        args = message.content.split(' ')[1:]
        if len(args) == 1:
            await play_song(message, args[0])
        elif len(args) >= 2:
            await play_song(message, args[0], ' '.join(args[1:]))
        else:
            await message.channel.send("Nem megfelelő formátum. Kérlek, adja meg a dal címét és opcionálisan az előadó nevét is.")

    elif message.content.startswith('!tovabb'):
        await skip_song(message)

    elif message.content.startswith('!sor'):
        await display_queue(message)

    elif message.content.startswith('!buhbye'):
        await buh_bye(message)

    elif message.content.startswith('!help'):
        await display_help(message)

client.run(TOKEN)
