import pytest

from app.core.config import get_settings
from app.infrastructure.clients import get_clients
from app.infrastructure.models import get_models
from app.services.retrieval import retrieve


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def clients(settings):
    return get_clients(settings)


@pytest.fixture(scope="session")
def models(settings):
    return get_models(settings)  


def test_retrieve_returns_sorted_hits(settings, clients, models):
    results = retrieve(
        query="Was ist der Bias-Varianz-Tradeoff?",
        clients=clients,
        models=models,
        top_k=settings.top_k,
        top_n=settings.top_n,
        collection=settings.collection,
    )

    assert results                                
    assert len(results) <= settings.top_n     
    scores = [chunk["rerank_score"] for chunk in results]
    required = {"title", "page_content", "page_reference_path", "rerank_score"}
    assert all(required <= chunk.keys() for chunk in results)
    assert scores == sorted(scores, reverse=True)     
    assert "page_content" in results[0]             
