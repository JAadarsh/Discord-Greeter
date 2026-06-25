"""
Data access object for all Supabase requests.
Credit: SUPABASE PTE. LTD. 2026
---------------------------------------------
Aadarsh Joshi 2026
"""

# database.py
from supabase import AsyncClient, acreate_client

class Database:
    """
    Notice: the class must be initialized with url and key within main.py.
    """
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client: AsyncClient = None

    async def connect(self):
        self.client = await acreate_client(self.url, self.key)

    """
    This is the section for the messenger. 
    Purpose is to send dms to specific users.
    """
    
    async def create_messenger_user(self, user_id: int):
        """Initializes or resets a messenger profile safely."""
        data_to_save = {
            "user_id": user_id,
            "recipient_list": [],  # stored in int8[] format in Supabase
            "universal_message": ""
        }
        # Using upsert instead of insert prevents duplicate key errors
        await self.client.table("messenger").upsert(data_to_save).execute()

    async def set_universal_message(self, user_id: int, message: str):
        """Updates or sets the message. Uses upsert to create row if missing."""
        await self.client.table("messenger").upsert({
            "user_id": user_id,
            "universal_message": message
        }).execute()

    async def get_universal_message(self, user_id: int) -> str:
        """Retrieves the universal message or returns empty string if missing."""
        response = await self.client.table("messenger").select("universal_message").eq("user_id", user_id).execute()
        if not response.data:
            return ""  # Default value for new users
        return response.data[0]["universal_message"]
    
    async def add_recipient(self, user_id: int, recipient_id: int):
        """Appends a user ID to the array safely, preventing duplicates."""
        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).execute()
        
        if not response.data:
            recipient_list = []
        else:
            recipient_list = response.data[0]["recipient_list"] or []
        
        if recipient_id not in recipient_list:
            recipient_list.append(recipient_id)
            # Upsert ensures data is saved even if user row didn't exist yet
            await self.client.table("messenger").upsert({
                "user_id": user_id,
                "recipient_list": recipient_list
            }).execute()

    async def remove_recipient(self, user_id: int, recipient_id: int):
        """Removes a user ID from the array if present."""
        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).execute()
        if not response.data:
            return  # No profile exists, nothing to remove
        
        recipient_list = response.data[0]["recipient_list"] or []
        
        if recipient_id in recipient_list:
            recipient_list.remove(recipient_id)
            await self.client.table("messenger").upsert({
                "user_id": user_id,
                "recipient_list": recipient_list
            }).execute()

    async def get_recipients(self, user_id: int) -> list:
        """Returns the list of stored recipient IDs."""
        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).execute()
        if not response.data:
            return []  # Default empty list for new users
        return response.data[0]["recipient_list"] or []