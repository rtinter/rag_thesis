from pathlib import Path
import json
import uuid
import numpy as np
from qdrant_client import models as qdrant_models
from fastembed import SparseEmbedding
from app.services.retrieval import combine_title_and_text
from app.core.config import get_settings
from app.infrastructure.models import get_models
from app.infrastructure.clients import get_qdrant, QdrantClient


root_dir = Path(__file__).parents[2]
data_dir = root_dir / "data" / "parsed_clean"
embedding_batch_size = 4

def load_chunks_from_json(data_dir: Path) -> list[dict]:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory {data_dir} does not exist.")
    chunks = []
    for json_file in data_dir.rglob("*.json"):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
            chunks.extend(data)
    return chunks

def confirm_overwrite(collection_name: str, qdrant_client: QdrantClient) -> None:
    if not qdrant_client.collection_exists(collection_name):
        return
    point_count = qdrant_client.count(collection_name=collection_name, exact=True).count
    print(
        f"Collection '{collection_name}' already exists and holds {point_count} points.\n"
        "Ingesting deletes it and rebuilds it from scratch."
    )
    answer = input("Type 'yes' to overwrite, anything else aborts: ").strip().lower()
    if answer != "yes":
        raise SystemExit("Aborted. Collection left untouched.")

def create_qdrant_collection(
    embeddings: list,
    collection_name: str,
    qdrant_client: QdrantClient
) -> None:
    if qdrant_client.collection_exists(collection_name):
        print(f"Recreating collection '{collection_name}'.")
        qdrant_client.delete_collection(collection_name)
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": qdrant_models.VectorParams(
                size=len(embeddings[0]),
                distance=qdrant_models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={         
            "sparse": qdrant_models.SparseVectorParams(
                modifier=qdrant_models.Modifier.IDF,
            ),
        },
    )
    
def build_qdrant_points(
    chunks: list[dict],
    dense_vectors: np.ndarray,
    sparse_vectors: list[SparseEmbedding],
) -> list[qdrant_models.PointStruct]:
    points = []
    for chunk, dense_vec, sparse_vec in zip(chunks, dense_vectors, sparse_vectors):
        points.append(
            qdrant_models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["id"])),
                vector={
                    "dense": dense_vec.tolist(),
                    "sparse": qdrant_models.SparseVector(
                        indices=sparse_vec.indices.tolist(),
                        values=sparse_vec.values.tolist(),
                    )
                },
                payload={
                    "chunk_id": chunk["id"],
                    "modul": chunk["modul"],
                    "lecture": chunk["lecture"],
                    "title": chunk["title"],
                    "page_content": chunk["page_content"],
                    "page_numbers": chunk["page_numbers"],
                    "page_reference_path": chunk["page_reference_path"],
                }, 
            )
        )
    return points


def main() -> None:
    settings = get_settings()
    qdrant_client = get_qdrant(settings)
    confirm_overwrite(settings.collection, qdrant_client)

    models = get_models(settings)
    chunks = load_chunks_from_json(data_dir)
    texts_to_embed = [combine_title_and_text(chunk) for chunk in chunks]
    
    dense_vectors = models.dense.encode(
        texts_to_embed, 
        normalize_embeddings=True, 
        batch_size=4,
        show_progress_bar=True, 
        )
    sparse_vectors = list(models.sparse.embed(texts_to_embed))
    
    create_qdrant_collection(
        embeddings=dense_vectors, 
        collection_name=settings.collection ,
        qdrant_client=qdrant_client
    )

    points = build_qdrant_points(
        chunks=chunks,
        dense_vectors=dense_vectors,
        sparse_vectors=sparse_vectors,
    )
    
    qdrant_client.upsert(collection_name=settings.collection, points=points)

if __name__ == "__main__":
    main()
    
    