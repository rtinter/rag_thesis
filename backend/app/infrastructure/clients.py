from dataclasses import dataclass
from openai import OpenAI
from qdrant_client import QdrantClient
from app.core.config import Settings

@dataclass
class Clients:
    qdrant: QdrantClient
    gateway: OpenAI

def get_qdrant(settings: Settings) -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)

def get_gateway(settings: Settings) -> OpenAI:
    return OpenAI(base_url=settings.gateway_url, api_key=settings.bearer_token, timeout=60)

def get_clients(settings: Settings) -> Clients:
    qdrant = get_qdrant(settings)
    gateway = get_gateway(settings)
    return Clients(qdrant=qdrant, gateway=gateway)
