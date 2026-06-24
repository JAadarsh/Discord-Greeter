"""
Copyright Aadarsh Joshi 2026 all rights reserved.
"""

import discord
import OpenRouterRequests
import os
import threading
import logging
from dotenv import load_dotenv
from discord.ext import commands
from http.server import BaseHTTPRequestHandler, HTTPServer
from SupabaseRequests import Database
from discord import app_commands

"""
This is to get around render's web hosting requirement.
Emulates a website. 
"""
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

threading.Thread(target=start_server, daemon=True).start()

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
command_guild_id = int(os.getenv('COMMAND_GUILD_ID')) if os.getenv('COMMAND_GUILD_ID') else None
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.all()

# command prefix is !, change later because its popular
bot = commands.Bot(command_prefix='!', intents=intents)

# -------------------------------------------------
# ^ This is the setup for bot & creating a server 
# v This is the actual bot stuff
# --------------------------------


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="We are open source! Check the github!"))
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')

    bot.db = Database(supabase_url, supabase_key)

    try:
        await bot.db.connect()
        print("Database connected.")
    except Exception as e:
        print(f"Error connecting to database: {e}")

    try:
        if command_guild_id:
            guild = discord.Object(id=command_guild_id)
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} guild slash commands to guild {command_guild_id}.")
        else:
            print("No COMMAND_GUILD_ID set; syncing global slash commands. Global commands can take up to 1 hour to appear.")
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} global slash commands.")

        registered = [command.name for command in bot.tree.walk_commands()]
        print(f"Registered slash command names: {registered}")
    except Exception as e:
        print(f"Command sync error: {e}")


# slash commands
@bot.tree.command(name="setmessage", description="Set your own custom greeting message!")
@app_commands.describe(text="The custom sentence or phrase you want to save")
async def setmessage(interaction: discord.Interaction, *, text: str):
    if len(text) > 1500:
        return await interaction.response.send_message("Message is too long. Please keep it under 1500 characters.", ephemeral=True)

    await bot.db.set_universal_message(interaction.user.id, text)
    await interaction.response.send_message("Universal message updated.")

@bot.tree.command(name="viewmessage", description="View current message")
async def viewmessage(interaction: discord.Interaction):
    message = await bot.db.get_universal_message(interaction.user.id)
    if message:
        await interaction.response.send_message(f"Current message is {message}")
    else:
        await interaction.response.send_message("No current message. Use /setmessage to set one.")

@bot.tree.command(name="add_recipient", description="Add someone to the mailing list")
@app_commands.describe(recipient="User to add to recipient list")
async def add_recipient(interaction: discord.Interaction, recipient: discord.User):
    await bot.db.add_recipient(interaction.user.id, recipient.id)
    await interaction.response.send_message(f"{recipient.name} has been added to your recipient list.")


"""
Section is mainly for testing, may be refined in a later update. 19 June 2026
"""
@bot.tree.command(name="say_something", description="Get an AI generated response")
@app_commands.describe(prompt="Prompt for the AI")
async def say_something(interaction: discord.Interaction, *, prompt: str):
    if len(prompt) > 500:
        return await interaction.response.send_message("Prompt is too long. Please keep it under 500 characters.", ephemeral=True)
    response = OpenRouterRequests.chat_devstral(prompt)
    await interaction.response.send_message(response)

bot.run(token)