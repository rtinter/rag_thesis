from app.services.retrieval import retrieve
from app.services.generation import generate, find_cited_markers
from app.infrastructure.clients import Clients
from app.infrastructure.models import Models
from app.core.config import Settings

def answer(
        question: str,
        clients: Clients,
        models: Models,
        settings: Settings,
) -> dict:
    chunks = retrieve(
        query=question,
        clients=clients,
        models=models,
        collection=settings.collection,
        top_k=settings.top_k,
        top_n=settings.top_n,
    )
    if not chunks:
        return {"question": question, "answer": "", "sources": [], "cited": []}
    
    llm_result = generate(
        question=question,
        chunks=chunks,
        gateway=clients.gateway,
        model=settings.inference_model,
    )
    
    cited = find_cited_markers(llm_result)
    sources = []
    for i, chunk in enumerate(chunks, start=1):
        chunk["cite_nr"] = i 
        chunk["cited"] = i in cited # cited or not?
        sources.append(chunk)

    return {
        "question": question,
        "answer": llm_result,
        "sources": sources,
        "cited": cited,
    }
