import os
import time
import random
import asyncio
import logging

import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
SERVER_HOST = os.getenv("SERVER_HOST", "hotc.secure.pebble.host")
SERVER_PORT = int(os.getenv("SERVER_PORT", "25565"))
GUILD_ID_RAW = os.getenv("GUILD_ID")

if not TOKEN:
    raise ValueError("Missing TOKEN environment variable")

if not GUILD_ID_RAW:
    raise ValueError("Missing GUILD_ID environment variable")

GUILD_ID = int(GUILD_ID_RAW)
BOT_START_TIME = time.time()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

server_online_since = None
last_server_online = None


async def get_status():
    try:
        server = JavaServer(SERVER_HOST, SERVER_PORT)
        status = await asyncio.to_thread(server.status)
        return status, None
    except Exception as e:
        return None, str(e)


def format_duration(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def clean_motd(description) -> str:
    if isinstance(description, str):
        return description

    if isinstance(description, dict):
        if description.get("text"):
            return description["text"]

        extra = description.get("extra")
        if isinstance(extra, list):
            parts = []
            for item in extra:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            if parts:
                return "".join(parts)

    return str(description)


@tasks.loop(seconds=30)
async def monitor_server():
    global server_online_since, last_server_online

    status_data, _ = await get_status()
    is_online = status_data is not None

    if is_online:
        if last_server_online is not True:
            server_online_since = time.time()
        last_server_online = True
    else:
        server_online_since = None
        last_server_online = False


@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    logging.info("Logged in as %s", bot.user)
    logging.info("Synced %s guild command(s)", len(synced))

    if not monitor_server.is_running():
        monitor_server.start()

@bot.tree.command(name="status", description="Check if the server is online")
async def status(interaction: discord.Interaction):
    status_data, _ = await get_status()
    if status_data is None:
        await interaction.response.send_message("Server is offline.")
    else:
        await interaction.response.send_message("Server is online.")


@bot.tree.command(name="playercount", description="Show current player count")
async def playercount(interaction: discord.Interaction):
    status_data, _ = await get_status()
    if status_data is None:
        await interaction.response.send_message("Server is offline.")
        return

    await interaction.response.send_message(
        f"Players: {status_data.players.online}/{status_data.players.max}"
    )

import random

@bot.tree.command(name="chudmeter", description="Measure chud levels")
async def chudmeter(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Zecrokunn is currently {random.randint(87,100)}% chudmaxxed."
    )
    
@bot.tree.command(name="ping", description="Show server ping")
async def ping(interaction: discord.Interaction):
    status_data, _ = await get_status()
    if status_data is None:
        await interaction.response.send_message("Server is offline.")
        return

    await interaction.response.send_message(f"Ping: {round(status_data.latency)} ms")


@bot.tree.command(name="version", description="Show server version")
async def version(interaction: discord.Interaction):
    status_data, _ = await get_status()
    if status_data is None:
        await interaction.response.send_message("Server is offline.")
        return

    await interaction.response.send_message(f"Version: {status_data.version.name}")


@bot.tree.command(name="motd", description="Show the server MOTD")
async def motd(interaction: discord.Interaction):
    status_data, _ = await get_status()
    if status_data is None:
        await interaction.response.send_message("Server is offline.")
        return

    await interaction.response.send_message(f"MOTD: {clean_motd(status_data.description)}")


@bot.tree.command(name="players", description="Show sample online players if available")
async def players(interaction: discord.Interaction):
    status_data, _ = await get_status()
    if status_data is None:
        await interaction.response.send_message("Server is offline.")
        return

    sample = getattr(status_data.players, "sample", None)
    if not sample:
        await interaction.response.send_message("No player sample available.")
        return

    names = [p.name for p in sample if hasattr(p, "name")]
    if not names:
        await interaction.response.send_message("No player sample available.")
        return

    await interaction.response.send_message("Players online sample: " + ", ".join(names))


@bot.tree.command(name="ip", description="Show the server IP")
async def ip(interaction: discord.Interaction):
    await interaction.response.send_message(f"{SERVER_HOST}:{SERVER_PORT}")


@bot.tree.command(name="uptime", description="Show bot uptime")
async def uptime(interaction: discord.Interaction):
    seconds = int(time.time() - BOT_START_TIME)
    await interaction.response.send_message(f"Bot uptime: {format_duration(seconds)}")

@bot.tree.command(name="chudmaxxers", description="List the local chudmaxxers")
async def chudmaxxers(interaction: discord.Interaction):
    await interaction.response.send_message(
        "heres a list of the local chudmaxxers: zecrokunn, zecrokunn, zecrokunn, zecrokunn, zecrokunn"
    )

@bot.tree.command(name="estimateduptime", description="Estimate how long the server has stayed online")
async def estimateduptime(interaction: discord.Interaction):
    status_data, _ = await get_status()
    if status_data is None:
        await interaction.response.send_message("Server is offline right now.")
        return

    if server_online_since is None:
        await interaction.response.send_message(
            "The server is online, but I have not tracked it long enough yet. Try again in about 30 seconds."
        )
        return

    seconds = int(time.time() - server_online_since)
    await interaction.response.send_message(
        f"Estimated server uptime: {format_duration(seconds)}\n"
        f"(Based on when the bot first detected the server online.)"
    )

@bot.tree.command(name="mommyasmr", description="Ask the cursed anime bot something")
async def mommyasmr(interaction: discord.Interaction, question: str):
    replies = [
        "nyahhh~ go touch grass, but softly...",
        "uwu the answer is hidden inside your router...",
        "*anime whisper* shhh... your server is eepy...",
        "nyaaa~ I asked the lag spirits and they said no >w<",
        "*pats your Minecraft server* it’s trying its best...",
        f"nyahhh~ `{question}` sounds very concerning uwu",
        f"*whispers softly* `{question}` is being processed by the silly braincell..."
    ]

    await interaction.response.send_message(random.choice(replies))

@bot.tree.command(name="commands", description="Show bot commands")
async def commands_list(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/status, /playercount, /ping, /version, /motd, /players, /ip, /uptime, /estimateduptime, /mommyasmr, /commands"
    )


@bot.event
async def on_error(event, *args, **kwargs):
    logging.exception("Unhandled error in event: %s", event)


bot.run(TOKEN, log_handler=None)
