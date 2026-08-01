from supabase import create_client, Client
from app.config import settings


class _LazySupabase:

    _client: Client = None

    def _get(self) -> Client:
        if self._client is None:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return self._client

    def __getattr__(self, name):
        return getattr(self._get(), name)

    def table(self, name):
        return self._get().table(name)


supabase = _LazySupabase()
