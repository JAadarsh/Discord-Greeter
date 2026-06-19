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
    Notice: the class must be initalized with url and key within main.py.
    """
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client = None

    async def connect(self):
        self.client = await acreate_client(self.url, self.key)

    """
    This is the section for the messenger. 
    Purpose is to send dms to specific users.
    """
    async def create_messenger_user(self, user_id:int):
        data_to_save = {
            "user_id": user_id,
            "recipient_list": [], # should be in user_id int format
            "universal_message": ""
        }
        await self.client.table("messenger").insert(data_to_save).execute()

    async def set_universal_message(self, user_id: int, message: str):
        await self.client.table("messenger").update({"universal_message": message}).eq("user_id", user_id).execute()

    async def get_universal_message(self, user_id: int) -> str:
        response = await self.client.table("messenger").select("universal_message").eq("user_id", user_id).execute()
        if not response.data:
            return ""  # Default value for new users
        return response.data[0]["universal_message"]
    
    async def add_recipient(self, user_id: int, recipient_id: int):
        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).execute()
        if not response.data:
            recipient_list = []
        else:
            recipient_list = response.data[0]["recipient_list"]
        
        if recipient_id not in recipient_list:
            recipient_list.append(recipient_id)
            await self.client.table("messenger").update({"recipient_list": recipient_list}).eq("user_id", user_id).execute()

    async def remove_recipient(self, user_id: int, recipient_id: int):
        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).execute()
        if not response.data:
            return  # No recipients to remove
        
        recipient_list = response.data[0]["recipient_list"]
        
        if recipient_id in recipient_list:
            recipient_list.remove(recipient_id)
            await self.client.table("messenger").update({"recipient_list": recipient_list}).eq("user_id", user_id).execute()

    async def get_recipients(self, user_id: int) -> list:
        response = await self.client.table("messenger").select("recipient_list").eq("user_id", user_id).execute()
        if not response.data:
            return []  # Default value for new users
        return response.data[0]["recipient_list"]

    async def set_universal_message(self, user_id: int, message: str):
        await self.client.table("messenger").update({"universal_message": message}).eq("user_id", user_id).execute()

    async def get_universal_message(self, user_id: int) -> str:
        response = await self.client.table("messenger").select("universal_message").eq("user_id", user_id).execute()
        if not response.data:
            return ""  # Default value for new users
        return response.data[0]["universal_message"]

