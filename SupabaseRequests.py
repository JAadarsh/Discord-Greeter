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

