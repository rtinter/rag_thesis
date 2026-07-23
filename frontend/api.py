import os

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def post_question(question: str) -> dict:
    response = httpx.post(
        f"{BACKEND_URL}/api/ask", json={"question": question}, timeout=120.0
    )
    response.raise_for_status()
    return response.json()


def build_slide_url(source: dict) -> str | None:
    path = source.get("slide_url")
    return f"{BACKEND_URL}{path}" if path else None
