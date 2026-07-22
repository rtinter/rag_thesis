from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gateway_url: str
    bearer_token: str

    qdrant_url: str = "http://localhost:6333"
    collection: str = "lecture_chunks"

    slides_dir: str = "../data/reference_slides"

    inference_model: str = "openai/gpt-oss-120b"
    vl_model: str = "Qwen/Qwen3.5-122B-A10B-GPTQ-Int4"
    dense_model: str = "BAAI/bge-m3"
    sparse_model: str = "Qdrant/bm25"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"

    top_k: int = 100  # candidates retrieved from Qdrant before reranking
    top_n: int = 5   # candidates kept after reranking

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    return Settings()
