from qdrant_client import models as qmodels

from app.infrastructure.clients import Clients
from app.infrastructure.models import Models

def combine_title_and_text(payload: dict) -> str:
    title = payload.get("title", "")
    page_content = payload.get("page_content", "")
    return f"{title}\n\n{page_content}"

def hybrid_search(
        query: str,
        clients: Clients,
        models: Models,
        top_k: int,
        collection: str,
) -> list[qmodels.ScoredPoint]:
    dense_vector = models.dense.encode(query, normalize_embeddings=True)
    sparse_vector = next(models.sparse.query_embed(query))
    
    return clients.qdrant.query_points(
        collection_name=collection,
        prefetch=[
            qmodels.Prefetch(
                query=dense_vector.tolist(), 
                using="dense", 
                limit=top_k
            ),
            qmodels.Prefetch(
                query=qmodels.SparseVector(
                    indices=sparse_vector.indices.tolist(),
                    values=sparse_vector.values.tolist(),
                ),
                using="sparse",
                limit=top_k,
            ),
        ],
        query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
        limit=top_k,
        with_payload=True,
    ).points

def retrieve(
        query: str,
        clients: Clients,
        models: Models,
        top_k: int,
        top_n: int,
        collection: str,
) -> list[dict]:
    candidates = hybrid_search(
        query=query,
        clients=clients,
        models=models,
        top_k=top_k,
        collection=collection,
    )
    if not candidates:
        return []
    
    pairs = [
        (query, combine_title_and_text(candidate.payload))
        for candidate in candidates
    ]

    scores = models.reranker.predict(pairs, batch_size=16)
    reranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True
    )

    results = []
    for candidate, score in reranked[:top_n]:
        chunk = dict(candidate.payload)
        chunk["rerank_score"] = float(score)
        results.append(chunk)

    return results
