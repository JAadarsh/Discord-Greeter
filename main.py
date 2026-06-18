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

bot.run(token)