"""Search API router."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from llm import detect_language, generate_contextual_response
from llm_batcher import batched_generate_response
from schemas import SearchRequest, SearchResponse
from search import search_verses

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)


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

        # Detect language for AI response from query text
        language = detect_language(request.query)

        # Generate AI response if we have results (using batching)
        ai_response = None
        ai_error = None

        if results.get("results"):
            try:
                ai_response = await batched_generate_response(
                    query=request.query,
                    verses=results["results"],
                    language=language,
                )

                # If no response was generated, provide helpful error
                if not ai_response:
                    ai_error = "AI response service temporarily unavailable. Please try again in a moment."
                    logger.warning(f"AI response generation returned None for query: {request.query[:50]}")

            except Exception as e:
                ai_error = "Failed to generate AI response. Please try again."
                logger.error(f"AI generation failed: {e}", exc_info=True)
        else:
            # No verses found
            ai_error = "No verses found matching your query. Try different keywords or check your spelling."
            logger.info(f"No results found for query: {request.query}")

        # Build response
        return SearchResponse(
            query_time_ms=results["query_time_ms"],
            results=results["results"],
            ai_response=ai_response,
            ai_error=ai_error,
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
