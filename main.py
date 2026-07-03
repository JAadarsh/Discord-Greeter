"""
Version 0.1.1
Copyright Aadarsh Joshi 2026 all rights reserved.
"""

import asyncio
import discord
import backend.openrouterpy.OpenRouterRequests as OpenRouterRequests
# import backend.openrouterpy.testfileOR as testfileOR # local testing only.
import os
import threading
import logging
import datetime
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer
from backend.supabase.SupabaseRequests import Database
from discord import app_commands
from discord.ext import tasks, commands

"""
IMPORTANT NOTICE - READ BEFORE DEPLOYING:
This bot should not be deployed in its current state.

Fixes made to the OR API. Response time is now around 3 seconds. 

BUT DO NOT DEPLOY THIS BOT.
Uploading to github for progress tracking incase I need to pull this back.
"""


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
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
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

    await bot.db.set_universal_message(interaction.user.id, interaction.guild_id, text)
    await interaction.response.send_message("Universal message updated.")

@bot.tree.command(name="viewmessage", description="View current message")
async def viewmessage(interaction: discord.Interaction):
    message = await bot.db.get_universal_message(interaction.user.id, interaction.guild_id)
    if message:
        await interaction.response.send_message(f"Current message is {message}")
    else:
        await interaction.response.send_message("No current message. Use /setmessage to set one.")

@bot.tree.command(name="add_recipient", description="Add someone to the mailing list")
@app_commands.describe(recipient="User to add to recipient list")
async def add_recipient(interaction: discord.Interaction, recipient: discord.User):
    await bot.db.add_recipient(interaction.user.id, interaction.guild_id, recipient.id)
    await interaction.response.send_message(f"{recipient.name} has been added to your recipient list.")

@bot.tree.command(name="say_something", description="Get an AI generated response")
@app_commands.describe(prompt="Prompt for the AI")
async def say_something(interaction: discord.Interaction, *, prompt: str):
    """
    This method is mainly to make sure that the bot works, will likely stay a feature or become a helper function soon. 
    """
    if len(prompt) > 500:
        return await interaction.response.send_message("Prompt is too long. Please keep it under 500 characters.", ephemeral=True)

    await interaction.response.defer(thinking=True)

    try:
        response = await asyncio.to_thread(OpenRouterRequests.response, prompt, True)
    except Exception as e:
        return await interaction.followup.send(f"Error {e}. Please contact the developer.", ephemeral=True)

    await interaction.followup.send(response)

def direct_message(user_id: int, message: str):
    """
    Helper method to send a dm to a user.
    """
    user = bot.get_user(user_id)
    if user:
        asyncio.create_task(user.send(message))
        return "completed"
    else:
        return f"User with ID {user_id} not found."

@bot.tree.command(name="set_time", description="Set a time for the bot to send a message")
@app_commands.describe(hour="Hour (0-23)", minute="Minute (0-59)")
async def set_time(interaction: discord.Interaction, hour: int, minute: int):
    """
    This method is to set a time for the bot to send a message. 
    """
    
    try: 
        if not (0 <= hour < 24) or not (0 <= minute < 60):
            raise ValueError("Invalid time format. Please use HH:MM in 24-hour format.")
    except ValueError as e:
        return await interaction.response.send_message(str(e), ephemeral=True)

    scheduled_time = datetime.datetime.combine(
        datetime.datetime.now(datetime.timezone.utc).date(),
        datetime.time(hour=hour, minute=minute, tzinfo=datetime.timezone.utc),
    )
    await bot.db.set_hours(interaction.user.id, interaction.guild_id, scheduled_time)
    await interaction.response.send_message(f"Time set to {hour:02d}:{minute:02d} for your messages.")

bot.run(token)