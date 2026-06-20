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
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')

    bot.db = Database(supabase_url, supabase_key)

    try:
        await bot.db.connect()
        print("Database connected.")
    except Exception as e:
        print(f"Error connecting to database: {e}")


# set the uni message through / or ! commands
@bot.hybrid_command(name="setmessage", description="Set your own custom greeting message!")
@app_commands.describe(text="The custom sentence or phrase you want to save")
async def universal_message(ctx: commands.Context, *, text: str):
    
    if len(text) > 1500:
        return await ctx.send("Message is too long. Please keep it under 1500 characters.")
        
    await bot.db.set_universal_message(ctx.author.id, text)
    await ctx.send("Universal message updated.")

@bot.hybrid_command(name="viewmessage", description="View current message")
@app_commands.describe("View current message")
async def view_message(ctx:commands.Context):
    message = await bot.db.get_universal_message(ctx.author.id)
    if message:
        await ctx.send(f"Current message is {message}")
    else:
        await ctx.send(f"No current message. Use /setmessage to set one.")

@bot.hybrid_command(name="add recipient", description="add someone to the mailing list")
@app_commands.describe(recipient="The user you want to add to the mailing list")
async def add_recipient(ctx:commands.Context, recipient: discord.User):
    await bot.db.add_recipient(ctx.author.id, recipient.id)
    await ctx.send(f"{recipient.name} has been added to your recipient list.")


"""
Section is mainly for testing, may be refined in a later update. 19 June 2026
"""
@bot.hybrid_command(name="say something", description="get an AI generated response")
@app_commands.describe(prompt="the prompt you want to send")
async def say_something(ctx:commands.Context, *, prompt:str):
    if len(prompt) > 500:
        return await ctx.send("Prompt is too long. Please keep it under 500 characters.")
    response = OpenRouterRequests.chat_devstral(prompt)
    await ctx.send(response)

bot.run(token)