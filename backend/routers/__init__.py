"""API routers for Bible RAG."""

from routers.health import router as health_router
from routers.metadata import router as metadata_router
from routers.search import router as search_router
from routers.themes import router as themes_router
from routers.verses import router as verses_router

__all__ = [
    "health_router",
    "metadata_router",
    "search_router",
    "themes_router",
    "verses_router",
]
