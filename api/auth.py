from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from database.supabase_client import supabase
from middleware.rate_limiter import rate_limiter
import jwt
import time
from datetime import datetime, timedelta


router = APIRouter(prefix="/auth", tags=["authentication"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


def create_access_token(user_id: str, email: str, expires_delta: timedelta = None) -> str:

    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow()
    }

    return jwt.encode(payload, "SECRET_KEY", algorithm="HS256")


def verify_token(token: str) -> dict:

    try:
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):

    rate_limit = rate_limiter.check_rate_limit(request)
    if not rate_limit["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {rate_limit['retry_after']} seconds"
        )

    try:
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name
                }
            }
        })

        if response.user:

            supabase.table("users").insert({
                "id": response.user.id,
                "email": request.email,
                "full_name": request.full_name,
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            access_token = create_access_token(response.user.id, request.email)

            return AuthResponse(
                success=True,
                message="Account created successfully",
                data={
                    "user": {
                        "id": response.user.id,
                        "email": request.email,
                        "full_name": request.full_name
                    },
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            )

        return AuthResponse(
            success=False,
            message="Signup failed. Please try again."
        )

    except Exception as e:
        error_msg = str(e)

        if "already registered" in error_msg.lower():
            raise HTTPException(status_code=409, detail="Email already registered")

        raise HTTPException(status_code=500, detail=f"Signup failed: {error_msg}")


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):

    rate_limit = rate_limiter.check_rate_limit(request)
    if not rate_limit["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {rate_limit['retry_after']} seconds"
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if response.user and response.session:

            supabase.table("users").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("id", response.user.id).execute()

            access_token = create_access_token(response.user.id, request.email)

            return AuthResponse(
                success=True,
                message="Login successful",
                data={
                    "user": {
                        "id": response.user.id,
                        "email": request.email,
                        "full_name": response.user.user_metadata.get("full_name")
                    },
                    "access_token": access_token,
                    "refresh_token": response.session.refresh_token,
                    "token_type": "bearer",
                    "expires_in": response.session.expires_in
                }
            )

        return AuthResponse(
            success=False,
            message="Invalid email or password"
        )

    except Exception as e:
        error_msg = str(e)

        if "invalid login" in error_msg.lower():
            raise HTTPException(status_code=401, detail="Invalid email or password")

        raise HTTPException(status_code=500, detail=f"Login failed: {error_msg}")


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: TokenRefreshRequest):

    try:
        response = supabase.auth.refresh_session({
            "refresh_token": request.refresh_token
        })

        if response.session:

            access_token = create_access_token(
                response.user.id,
                response.user.email
            )

            return AuthResponse(
                success=True,
                message="Token refreshed successfully",
                data={
                    "access_token": access_token,
                    "refresh_token": response.session.refresh_token,
                    "token_type": "bearer",
                    "expires_in": response.session.expires_in
                }
            )

        return AuthResponse(
            success=False,
            message="Token refresh failed"
        )

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout", response_model=AuthResponse)
async def logout(request: Request):

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]

    try:
        payload = verify_token(token)

        supabase.auth.sign_out()

        return AuthResponse(
            success=True,
            message="Logged out successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        return AuthResponse(
            success=True,
            message="Logged out successfully"
        )


@router.get("/me", response_model=AuthResponse)
async def get_current_user(request: Request):

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]

    payload = verify_token(token)

    user_id = payload.get("sub")

    response = (
        supabase
        .table("users")
        .select("*")
        .eq("id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    user = response.data[0]

    return AuthResponse(
        success=True,
        message="User retrieved successfully",
        data={
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name"),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
        }
    )


@router.put("/profile", response_model=AuthResponse)
async def update_profile(request: Request, full_name: Optional[str] = None):

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    user_id = payload.get("sub")

    update_data = {}
    if full_name:
        update_data["full_name"] = full_name

    if update_data:
        supabase.table("users").update(update_data).eq("id", user_id).execute()

    return AuthResponse(
        success=True,
        message="Profile updated successfully"
    )
