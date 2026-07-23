"""
Version 0.1.5
Copyright Aadarsh Joshi 2026 all rights reserved.
"""

import asyncio
import discord
from backend.openrouterpy import openrouterrequests as OpenRouterRequests
import os
import logging
import datetime
from dotenv import load_dotenv
from backend.supabase.SupabaseRequests import Database
from backend.timezones import COMMON_TIMEZONES
from discord import app_commands
from discord.ext import tasks, commands

try:
    from zoneinfo import ZoneInfo, available_timezones, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover
    ZoneInfo = None
    available_timezones = lambda: set()
    class ZoneInfoNotFoundError(Exception):
        pass

try:
    from dateutil.tz import gettz
except ImportError:
    gettz = None

try:
    import pytz
except ImportError:
    pytz = None

"""
Notice:
Bot is incomplete, but can be deployed.
"""

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.all()

# command prefix is !, change later because its popular
bot = commands.Bot(command_prefix='!', intents=intents)


# -------------------------------------------------
# ^ This is the setup for bot 
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

async def timezone_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocomplete for common timezone names."""
    lower_query = current.lower() if current else ""
    matches = [tz for tz in COMMON_TIMEZONES if lower_query in tz.lower()]
    return [app_commands.Choice(name=tz, value=tz) for tz in matches[:25]]

def resolve_timezone(timezone_name: str):
    """Resolve a timezone by name using zoneinfo or dateutil/pytz fallback."""
    if not timezone_name:
        raise ValueError("Timezone name is required.")

    zoneinfo_error = None
    if ZoneInfo is not None:
        try:
            return ZoneInfo(timezone_name)
        except Exception as e:
            zoneinfo_error = e

    if gettz is not None:
        timezone = gettz(timezone_name)
        if timezone is not None:
            return timezone

    if pytz is not None:
        try:
            return pytz.timezone(timezone_name)
        except Exception:
            pass

    package_suggestions = []
    if gettz is None:
        package_suggestions.append("python-dateutil")
    if pytz is None:
        package_suggestions.append("pytz")
    package_suggestions.append("tzdata")
    packages_text = ", ".join(package_suggestions)

    message = f"No time zone found with key {timezone_name}."
    if zoneinfo_error is not None:
        message += f" ZoneInfo error: {zoneinfo_error}."
    message += (
        f" Please install one of {packages_text} and restart the bot, or use a supported timezone from autocomplete."
    )
    raise ValueError(message)


def localize_datetime(timezone_obj, year: int, month: int, day: int, hour: int, minute: int) -> datetime.datetime:
    if hasattr(timezone_obj, "localize"):
        return timezone_obj.localize(datetime.datetime(year, month, day, hour, minute, 0))
    return datetime.datetime(year, month, day, hour, minute, 0, tzinfo=timezone_obj)


def next_scheduled_utc(scheduled_timezone: str, hour: int, minute: int, after: datetime.datetime | None = None) -> datetime.datetime:
    if after is None:
        after = datetime.datetime.now(datetime.timezone.utc)
    if after.tzinfo is None:
        after = after.replace(tzinfo=datetime.timezone.utc)

    zone = resolve_timezone(scheduled_timezone)
    now_local = after.astimezone(zone)
    candidate_local = localize_datetime(zone, now_local.year, now_local.month, now_local.day, hour, minute)

    if candidate_local <= now_local:
        candidate_local = candidate_local + datetime.timedelta(days=1)

    return candidate_local.astimezone(datetime.timezone.utc)


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
        scheduled_timezone = entry.get("scheduled_timezone")
        scheduled_time = entry.get("timestamp")

        # Skip if message is empty
        if not message or not message.strip():
            continue

        # Send the message to each recipient
        try:
            for recipient_id in recipient_list:
                direct_message(recipient_id, message)
        except Exception as e:
            print(f"Error sending message to user {recipient_id}: {e}")

        if scheduled_timezone and scheduled_time:
            try:
                if isinstance(scheduled_time, str):
                    scheduled_time = datetime.datetime.fromisoformat(scheduled_time)
                    if scheduled_time.tzinfo is None:
                        scheduled_time = scheduled_time.replace(tzinfo=datetime.timezone.utc)

                local_zone = resolve_timezone(scheduled_timezone)
                local_scheduled = scheduled_time.astimezone(local_zone)
                next_timestamp = next_scheduled_utc(
                    scheduled_timezone,
                    local_scheduled.hour,
                    local_scheduled.minute,
                    after=now,
                )
                await bot.db.set_hours(user_id, guild_id, next_timestamp, scheduled_timezone)
            except Exception as e:
                print(f"Error rescheduling daily message for {user_id} in {guild_id}: {e}")

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
@app_commands.describe(hour="Hour (0-23)", minute="Minute (0-59)", timezone="Time zone for your scheduled message")
@app_commands.autocomplete(timezone=timezone_autocomplete)
async def set_time(interaction: discord.Interaction, hour: int, minute: int, timezone: str):
    """
    This method is to set a time for the bot to send a message. 
    """
    if not (0 <= hour < 24) or not (0 <= minute < 60):
        return await interaction.response.send_message(
            "Invalid time format. Please use HH:MM in 24-hour format.", ephemeral=True
        )

    if timezone not in COMMON_TIMEZONES:
        return await interaction.response.send_message(
            "Invalid timezone. Choose a supported zone or use autocomplete.", ephemeral=True
        )

    try:
        local_zone = resolve_timezone(timezone)
    except ValueError as e:
        return await interaction.response.send_message(str(e), ephemeral=True)

    local_date = datetime.datetime.now(local_zone).date()
    local_time = datetime.datetime(
        local_date.year,
        local_date.month,
        local_date.day,
        hour,
        minute,
        tzinfo=local_zone,
    )
    scheduled_time = local_time.astimezone(datetime.timezone.utc)

    await bot.db.set_hours(
        interaction.user.id,
        interaction.guild_id,
        scheduled_time,
        scheduled_timezone=timezone,
    )
    await interaction.response.send_message(
        f"Time set to {hour:02d}:{minute:02d} ({timezone}) which is {scheduled_time.strftime('%H:%M UTC')} UTC."
    )

bot.run(token)