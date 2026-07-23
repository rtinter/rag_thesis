from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.infrastructure.clients import get_clients
from app.infrastructure.models import get_models
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.clients = get_clients(settings)
    app.state.models = get_models(settings)
    print("API docs: http://localhost:8000/docs", flush=True)
    yield  

app = FastAPI(title="RAG Backend", lifespan=lifespan)
app.include_router(router)
app.mount("/slides", StaticFiles(directory=get_settings().slides_dir), name="slides")
