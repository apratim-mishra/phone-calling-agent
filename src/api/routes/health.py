from datetime import datetime

from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow(),
    )


@router.get("/health/detailed")
async def detailed_health() -> dict:
    """Detailed health check with component status."""
    components = {
        "api": "healthy",
        "database": "unknown",
        "pinecone": "unknown",
        "llm": "unknown",
    }

    if settings.primary_llm_available or settings.fallback_llm_available:
        components["llm"] = "configured"
    else:
        components["llm"] = "not_configured"

    if settings.pinecone_api_key:
        components["pinecone"] = "configured"
    else:
        components["pinecone"] = "not_configured"

    if settings.database_url:
        components["database"] = "configured"

    overall = "healthy" if all(v != "error" for v in components.values()) else "degraded"

    return {
        "status": overall,
        "components": components,
        "timestamp": datetime.utcnow().isoformat(),
    }

