from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.config import settings
from src.database import init_db
from src.utils.logging import setup_logging, get_logger
from src.utils.monitoring import monitor

load_dotenv()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    setup_logging()
    logger.info(f"Starting {settings.app_name}")

    await init_db()
    logger.info("Database initialized")

    if settings.wandb_enabled:
        monitor.init(
            run_name=f"{settings.app_name}-server",
            config={"app_name": settings.app_name, "debug": settings.debug},
        )

    yield

    monitor.finish()
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title="Realtime Phone Agent API",
    description="AI-powered phone agent with real-time voice processing",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routes import health, voice, webhooks

app.include_router(health.router)
app.include_router(voice.router)
app.include_router(webhooks.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }

