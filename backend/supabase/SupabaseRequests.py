"""
Data access object for all Supabase requests.
Credit: SUPABASE PTE. LTD. 2026
---------------------------------------------
Aadarsh Joshi 2026
"""

# database.py
import datetime
from supabase import AsyncClient, acreate_client

class Database:
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client: AsyncClient = None

    async def connect(self):
        self.client = await acreate_client(self.url, self.key)
    
    async def create_messenger_user(self, user_id: int, guild_id: int):
        """Initializes or resets a messenger profile safely for a specific guild."""
        
        data_to_save = {
            "user_id": user_id,
            "guild_id": guild_id,
            "recipient_list": [],  # stored in int8[] format in Supabase
            "universal_message": ""
        }
        await self.client.table("messenger").upsert(data_to_save).execute()

    async def set_universal_message(self, user_id: int, guild_id: int, message: str):
        """Updates or sets the message while ensuring the recipient list is initialized."""

        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).eq("guild_id", guild_id).execute()
        if response.data:
            recipient_list = response.data[0].get("recipient_list") or []
        else:
            recipient_list = []

        await self.client.table("messenger").upsert({
            "user_id": user_id,
            "guild_id": guild_id,
            "recipient_list": recipient_list,
            "universal_message": message or ""
        }).execute()

    async def get_universal_message(self, user_id: int, guild_id: int) -> str:
        """Retrieves the universal message or returns empty string if missing."""

        response = await self.client.table("messenger").select("universal_message").eq("user_id", user_id).eq("guild_id", guild_id).execute()
        if not response.data:
            return ""  # Default value for new users
        return response.data[0]["universal_message"]
    
    async def add_recipient(self, user_id: int, guild_id: int, recipient_id: int):
        """Appends a user ID to the array safely, preventing duplicates."""

        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).eq("guild_id", guild_id).execute()
        
        if not response.data:
            recipient_list = []
        else:
            recipient_list = response.data[0]["recipient_list"] or []
        
        if recipient_id not in recipient_list:
            recipient_list.append(recipient_id)
            # Upsert ensures data is saved even if user row didn't exist yet
            await self.client.table("messenger").upsert({
                "user_id": user_id,
                "guild_id": guild_id,
                "recipient_list": recipient_list
            }).execute()

    async def remove_recipient(self, user_id: int, guild_id: int, recipient_id: int):
        """Removes a user ID from the array if present."""

        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).eq("guild_id", guild_id).execute()
        if not response.data:
            return  # No profile exists, nothing to remove
        
        recipient_list = response.data[0]["recipient_list"] or []
        
        if recipient_id in recipient_list:
            recipient_list.remove(recipient_id)
            await self.client.table("messenger").upsert({
                "user_id": user_id,
                "guild_id": guild_id,
                "recipient_list": recipient_list
            }).execute()

    async def get_recipients(self, user_id: int, guild_id: int) -> list:
        """Returns the list of stored recipient IDs."""

        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).eq("guild_id", guild_id).execute()
        if not response.data:
            return []  # Default empty list for new users
        return response.data[0]["recipient_list"] or []
    
    async def set_hours(self, user_id: int, guild_id: int, scheduled_time: datetime.datetime):
        """Sets the scheduled timestamp for the user."""
        if isinstance(scheduled_time, datetime.datetime):
            if scheduled_time.tzinfo is None:
                scheduled_time = scheduled_time.replace(tzinfo=datetime.timezone.utc)
            scheduled_time = scheduled_time.isoformat()

        await self.client.table("messenger").upsert({
            "user_id": user_id,
            "guild_id": guild_id,
            "scheduled_time": scheduled_time
        }).execute()