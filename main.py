"""
Version 0.1.4
Copyright Aadarsh Joshi 2026 all rights reserved.
"""

import asyncio
import discord
import backend.openrouterpy.OpenRouterRequests as OpenRouterRequests
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
Notice:
Bot is incomplete, but can be deployed.
"""


"""
TODO: verify if we need this. Switched from render to Wispbyte.
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

# looping tasks

def direct_message(user_id: int, message: str):
    """
    Helper method to send a dm to a user.
    """
    if not message or not message.strip():
        return "Message is empty, skipping."
    
    user = bot.get_user(user_id)
    if user:
        asyncio.create_task(user.send(message))
        return "completed"
    else:
        return f"User with ID {user_id} not found."

@tasks.loop(minutes=1)
async def check_scheduled_messages():
    """
    checks scheduled messages every minute
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    response = await bot.db.get_scheduled_messages(now)
    
    for entry in response:
        user_id = entry["user_id"]
        guild_id = entry["guild_id"]
        message = entry["universal_message"]
        recipient_list = entry["recipient_list"]

        # Skip if message is empty
        if not message or not message.strip():
            continue

        # Send the message to each recipient
        try:
            for recipient_id in recipient_list:
                direct_message(recipient_id, message)
        except Exception as e:
            print(f"Error sending message to user {recipient_id}: {e}")

def looping_tasks():
    """
    helper method to start all looping tasks
    (yes I know there's only one)
    """
    check_scheduled_messages.start()

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="We are open source! Check the github!"))
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')

    # database connection
    bot.db = Database(supabase_url, supabase_key)
    try:
        await bot.db.connect()
        print("Database connected.")
    except Exception as e:
        print(f"Error connecting to database: {e}")

    # / cmds
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global slash commands.")

        registered = [command.name for command in bot.tree.walk_commands()]
        print(f"Registered slash command names: {registered}")
    except Exception as e:
        print(f"Command sync error: {e}")

    # looping tasks
    looping_tasks()

# slash commands
@bot.tree.command(name="set_message", description="Set your own custom greeting message!")
@app_commands.describe(text="The custom sentence or phrase you want to save")
async def set_message(interaction: discord.Interaction, *, text: str):
    if len(text) > 1500:
        return await interaction.response.send_message("Message is too long. Please keep it under 1500 characters.", ephemeral=True)

    await bot.db.set_universal_message(interaction.user.id, interaction.guild_id, text)
    await interaction.response.send_message("Universal message updated.")

@bot.tree.command(name="view_message", description="View current message")
async def view_message(interaction: discord.Interaction):
    message = await bot.db.get_universal_message(interaction.user.id, interaction.guild_id)
    if message:
        await interaction.response.send_message(f"Current message is {message}")
    else:
        await interaction.response.send_message("No current message. Use /set_message to set one.")

@bot.tree.command(name="add_recipient", description="Add someone to the mailing list")
@app_commands.describe(recipient="User to add to recipient list")
async def add_recipient(interaction: discord.Interaction, recipient: discord.User):
    await bot.db.add_recipient(interaction.user.id, interaction.guild_id, recipient.id)
    await interaction.response.send_message(f"{recipient.name} has been added to your recipient list.")

@bot.tree.command(name="remove_recipient", description="Remove someone from the mailing list")
@app_commands.describe(recipient="User to remove from recipient list")
async def remove_recipient(interaction: discord.Interaction, recipient: discord.User):
    await bot.db.remove_recipient(interaction.user.id, interaction.guild_id, recipient.id)
    await interaction.response.send_message(f"{recipient.name} has been removed from your recipient list.")

@bot.tree.command(name="clear_recipients", description="Clear the recipient list")
async def clear_recipients(interaction: discord.Interaction):
    await bot.db.clear_recipients(interaction.user.id, interaction.guild_id)
    await interaction.response.send_message("Recipient list cleared.")

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

    if not response or not response.strip():
        return await interaction.followup.send("AI returned an empty response. Please try again.", ephemeral=True)

    await interaction.followup.send(response)

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