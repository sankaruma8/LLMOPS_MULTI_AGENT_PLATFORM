from supabase import create_client, Client
from app.config import settings
from typing import Optional


class SupabasePool:

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:

        if cls._instance is None:
            cls._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )

        return cls._instance

    @classmethod
    def reset(cls):

        cls._instance = None


def get_supabase() -> Client:
    return SupabasePool.get_client()


supabase = get_supabase()
