from http.client import HTTPException

from fastapi import APIRouter, Request

from app.api.schemas import QuestionRequest, QuestionResponse, Source
from app.services.pipeline import answer

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

def to_slide_url(page_reference_path: str) -> str | None:
    if not page_reference_path:
        return None
    return page_reference_path.replace("data/reference_slides", "/slides")

@router.post("/ask")
def ask(payload: QuestionRequest, request: Request) -> QuestionResponse:
    state = request.app.state
    try:
        result = answer(
            payload.question,
            clients=state.clients,
            models=state.models,
            settings=state.settings,
        )

    except Exception:
        logger.exception("/ask -> answer() failed for question : %r", payload.question)
        raise HTTPException(
            status_code=502,
            detail="Nachricht konnte nicht verarbeitet werden. Bitte erneut versuchen.",
        )

    sources = [
        Source(
            cite_nr=chunk["cite_nr"],
            chunk_id=chunk["chunk_id"],
            modul=chunk["modul"],
            lecture=chunk["lecture"],
            title=chunk["title"],
            page_numbers=chunk["page_numbers"],
            slide_url=to_slide_url(chunk["page_reference_path"]),
            cited=chunk["cited"],
            rerank_score=chunk["rerank_score"],
        )
        for chunk in result["sources"]
    ]

    return QuestionResponse(
        question=result["question"],
        answer=result["answer"],
        sources=sources,
        cited=result["cited"],
    )

@router.get("/health")
def health(request: Request):
    qdrant = request.app.state.clients.qdrant
    try:
        qdrant.get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False
    return {"status": "ok" if qdrant_ok else "error", "qdrant_ok": qdrant_ok}

