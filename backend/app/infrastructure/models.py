from dataclasses import dataclass
from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer, CrossEncoder
import torch
from app.core.config import Settings

@dataclass
class Models:
    dense: SentenceTransformer
    sparse: SparseTextEmbedding
    reranker: CrossEncoder

def resolve_device() -> str:
    if torch.cuda.is_available():
        return "cuda"           
    if torch.backends.mps.is_available():
        return "mps"              
    return "cpu"                 

def get_dense_model(settings: Settings, device: str) -> SentenceTransformer:
    return SentenceTransformer(settings.dense_model, device=device)

def get_sparse_model(settings: Settings) -> SparseTextEmbedding:
    return SparseTextEmbedding(settings.sparse_model, language="german")

def get_reranker_model(settings: Settings, device: str) -> CrossEncoder:
    reranker = CrossEncoder(settings.rerank_model, device=device)
    if device == "cuda":
        reranker.model.half() # fp16: only useful on NVIDIA GPUs - used in notebooks for evaulation with good speed
    return reranker

def get_models(settings: Settings) -> Models:
    device = resolve_device()
    return Models(
        dense=get_dense_model(settings, device),
        sparse=get_sparse_model(settings),
        reranker=get_reranker_model(settings, device),
    )