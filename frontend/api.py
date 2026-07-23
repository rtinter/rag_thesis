import os

import httpx

backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")


def post_question(question: str) -> dict:
    response = httpx.post(
        f"{backend_url}/api/ask", json={"question": question}, timeout=120.0
    )
    response.raise_for_status()
    return response.json()

def get_slide(url: str) -> bytes:
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    return response.content

def build_slide_url(source: dict) -> str | None:
    path = source.get("slide_url")
    return f"{backend_url}{path}" if path else None

