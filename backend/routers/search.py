"""Search API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from llm import detect_language, generate_contextual_response
from llm_batcher import batched_generate_response
from schemas import SearchRequest, SearchResponse
from search import search_verses

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
):
    """Perform semantic search across Bible translations.

    Search for verses using natural language queries in English or Korean.
    Returns relevant verses ranked by semantic similarity.
    """
    try:
        # Convert filters to dict if present
        filters = None
        if request.filters:
            filters = {
                "testament": request.filters.testament,
                "genre": request.filters.genre,
                "books": request.filters.books,
            }
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}

        # Perform search
        results = search_verses(
            db=db,
            query=request.query,
            translations=request.translations,
            max_results=request.max_results,
            filters=filters if filters else None,
            include_original=request.include_original,
            include_cross_refs=True,
        )

        # Detect language for AI response
        language = detect_language(request.query)
        if "ko" in request.languages:
            language = "ko"

        # Generate AI response if we have results (using batching)
        ai_response = None
        if results.get("results"):
            ai_response = await batched_generate_response(
                query=request.query,
                verses=results["results"],
                language=language,
            )

        # Build response
        return SearchResponse(
            query_time_ms=results["query_time_ms"],
            results=results["results"],
            ai_response=ai_response,
            search_metadata={
                "total_results": results["search_metadata"]["total_results"],
                "embedding_model": results["search_metadata"].get("embedding_model"),
                "cached": results.get("cached", False),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e),
            },
        )
