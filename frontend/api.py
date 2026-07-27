import os
import httpx

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


async def api_get(path: str, token: str = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_URL}{path}", headers=headers)
        return resp.json()


async def api_post(path: str, data: dict = None, token: str = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{API_URL}{path}", json=data or {}, headers=headers)
        return resp.json()


def api_post_sync(path: str, data: dict = None, token: str = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=600) as client:
        resp = client.post(f"{API_URL}{path}", json=data or {}, headers=headers)
        return resp.json()


def api_get_sync(path: str, token: str = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{API_URL}{path}", headers=headers)
        return resp.json()


def upload_file_sync(file_bytes, filename, token: str = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=600) as client:
        resp = client.post(
            f"{API_URL}/upload",
            files={"file": (filename, file_bytes, "application/pdf")},
            headers=headers
        )
        return resp.json()
