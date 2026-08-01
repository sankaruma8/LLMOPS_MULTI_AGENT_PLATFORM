import asyncio
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from app.config import settings

security = HTTPBearer(auto_error=False)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")

    from database.supabase_client import supabase
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: supabase.table("users").select("*").eq("id", user_id).execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    return response.data[0]


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")

    from database.supabase_client import supabase
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: supabase.table("users").select("*").eq("id", user_id).execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    return response.data[0]
