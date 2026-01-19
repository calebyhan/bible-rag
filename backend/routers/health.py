"""Health check API router."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from cache import get_cache
from config import get_settings
from database import Embedding, Translation, Verse, get_db
from schemas import HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint.

    Returns the status of all services and basic statistics.
    """
    services = {}
    errors = []
    stats = {}

    # Check database
    try:
        db.execute(text("SELECT 1"))
        services["database"] = "healthy"

        # Get stats
        stats["total_verses"] = db.query(Verse).count()
        stats["total_translations"] = db.query(Translation).count()
        stats["total_embeddings"] = db.query(Embedding).count()
    except Exception as e:
        services["database"] = "unhealthy"
        errors.append(f"Database error: {str(e)}")

    # Check Redis
    try:
        cache = get_cache()
        if cache.is_connected():
            services["redis"] = "healthy"
            cache_stats = cache.get_cache_stats()
            stats["cache_keys"] = cache_stats.get("cached_searches", 0)
        else:
            services["redis"] = "unhealthy"
            errors.append("Redis connection failed")
    except Exception as e:
        services["redis"] = "unhealthy"
        errors.append(f"Redis error: {str(e)}")

    # Report embedding mode and model
    try:
        # Report embedding mode (local vs gemini)
        services["embedding_mode"] = settings.embedding_mode
        services["embedding_model"] = settings.embedding_model

        # Check if model is loaded (only for local mode)
        if settings.embedding_mode == "local":
            from embeddings import get_embedding_model

            # Don't actually load the model here, just check if it's cached
            import functools

            if hasattr(get_embedding_model, "cache_info"):
                cache_info = get_embedding_model.cache_info()
                if cache_info.hits > 0 or cache_info.currsize > 0:
                    services["embedding_status"] = "loaded"
                else:
                    services["embedding_status"] = "not_loaded"
            else:
                services["embedding_status"] = "unknown"
        else:
            services["embedding_status"] = "api"
    except Exception as e:
        services["embedding_status"] = f"error: {str(e)}"

    # Determine overall status
    overall_status = "healthy"
    if "unhealthy" in services.values():
        overall_status = "unhealthy"
    elif services.get("embedding_status") == "not_loaded":
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services=services,
        stats=stats if stats else None,
        errors=errors if errors else None,
    )
