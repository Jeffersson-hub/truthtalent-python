# lib/config.py
import os
from typing import Optional

class Config:
    @staticmethod
    def get_supabase_url() -> str:
        return os.getenv('SUPABASE_URL', '')
    
    @staticmethod
    def get_supabase_key() -> str:
        return os.getenv('SUPABASE_SERVICE_KEY', '')
    
    @staticmethod
    def is_vercel() -> bool:
        return bool(os.getenv('VERCEL', ''))
    
    @staticmethod
    def get_environment() -> str:
        return "vercel" if Config.is_vercel() else "local"