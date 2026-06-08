"""
OmniCX — Agentic AI for Seamless Omnichannel Customer Experience
FastAPI application entry point
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.routes import router as api_router
from api.websocket import router as ws_router
from core.event_bus import EventBus
from db.chroma_client import ChromaClient
from db.redis_client import RedisClient

log = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("omnicx.startup", env=settings.app_env)
    app.state.redis    = await RedisClient.connect(settings.redis_url)
    app.state.chroma   = ChromaClient(settings.chroma_host, settings.chroma_port)
    app.state.event_bus = EventBus()
    log.info("omnicx.ready")
    yield
    await app.state.redis.aclose()
    log.info("omnicx.shutdown")


app = FastAPI(
    title="OmniCX API",
    description="Agentic AI for Seamless Omnichannel Customer Experience",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router,  prefix="/ws", tags=["WebSocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
