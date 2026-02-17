"""Search API router."""

import logging
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from llm import detect_language, expand_query, generate_contextual_response
from llm_batcher import batched_generate_response
from schemas import SearchRequest, SearchResponse
from search import search_verses

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/search")
async def semantic_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    x_gemini_api_key: str | None = Header(None, alias="X-Gemini-API-Key"),
    x_groq_api_key: str | None = Header(None, alias="X-Groq-API-Key"),
):
    """Perform semantic search across Bible translations.

    Streams results and then AI response chunks using NDJSON.
    """
    import json
    from fastapi.responses import StreamingResponse
    from llm import generate_contextual_response_stream

    async def response_generator():
        try:
            # Convert filters to dict if present
            filters = None
            if request.filters:
                filters = {
                    "testament": request.filters.testament,
                    "genre": request.filters.genre,
                    "books": request.filters.books,
                }
                filters = {k: v for k, v in filters.items() if v is not None}

            # Query expansion: generate alternative search queries
            expanded_queries = []
            if settings.enable_query_expansion:
                expanded_queries = await expand_query(
                    query=request.query,
                    language=detect_language(request.query),
                    groq_api_key=x_groq_api_key,
                    gemini_api_key=x_gemini_api_key,
                )

            # Perform search with hybrid retrieval + RRF
            results = await search_verses(
                db=db,
                query=request.query,
                translations=request.translations,
                max_results=request.max_results,
                filters=filters if filters else None,
                include_original=request.include_original,
                include_cross_refs=True,
                api_key=x_gemini_api_key,
                expanded_queries=expanded_queries,
            )

            # Send search results first
            search_response = {
                "type": "results",
                "data": {
                    "query_time_ms": results["query_time_ms"],
                    "results": results["results"],
                    "search_metadata": results["search_metadata"],
                }
            }
            yield json.dumps(search_response) + "\n"

            # Detect language and generate AI response stream
            if results.get("results"):
                language = detect_language(request.query)
                
                # Build conversation history dicts from request
                history = None
                if request.conversation_history:
                    history = [
                        {"role": t.role, "content": t.content}
                        for t in request.conversation_history
                    ]

                # Stream tokens
                async for token in generate_contextual_response_stream(
                    query=request.query,
                    verses=results["results"],
                    language=language,
                    gemini_api_key=x_gemini_api_key,
                    groq_api_key=x_groq_api_key,
                    conversation_history=history,
                ):
                    if token:
                        msg = {"type": "token", "content": token}
                        yield json.dumps(msg) + "\n"
            
            # Send done signal (optional but helpful)
            # yield json.dumps({"type": "done"}) + "\n"

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(response_generator(), media_type="application/x-ndjson")
