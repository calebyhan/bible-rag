"""FastAPI application for Bible RAG.

Main entry point for the API server.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import (
    health_router,
    metadata_router,
    search_router,
    themes_router,
    verses_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    print("Starting Bible RAG API...")

    # Optionally preload the embedding model
    # Uncomment to preload at startup (uses ~4GB RAM)
    # from embeddings import get_embedding_model
    # print("Preloading embedding model...")
    # get_embedding_model()
    # print("Embedding model loaded!")

    yield

    # Shutdown
    print("Shutting down Bible RAG API...")


# Create FastAPI app
app = FastAPI(
    title="Bible RAG API",
    description="Multilingual Bible study platform powered by semantic search",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "https://bible-rag.vercel.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(search_router)
app.include_router(verses_router)
app.include_router(themes_router)
app.include_router(metadata_router)


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "Bible RAG API",
        "version": "1.0.0",
        "description": "Multilingual Bible study platform powered by semantic search",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
