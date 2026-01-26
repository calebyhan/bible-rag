"""Themes API router."""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import ThemeRequest, ThemeResponse
from search import search_by_theme

router = APIRouter(prefix="/api", tags=["themes"])


@router.post("/themes", response_model=ThemeResponse)
async def thematic_search(
    request: ThemeRequest,
    db: AsyncSession = Depends(get_db),
    x_gemini_api_key: str | None = Header(None, alias="X-Gemini-API-Key"),
):
    """Search for verses by theme.

    Perform thematic search across the Bible with optional
    testament filtering.

    Args:
        request: Theme search parameters

    Returns:
        Verses matching the theme
    """
    try:
        results = await search_by_theme(
            db=db,
            theme=request.theme,
            translations=request.translations,
            testament=request.testament if request.testament != "both" else None,
            max_results=request.max_results,
            api_key=x_gemini_api_key,
        )

        return ThemeResponse(
            theme=results.get("theme", request.theme),
            testament_filter=results.get("testament_filter"),
            query_time_ms=results["query_time_ms"],
            results=results["results"],
            total_results=results["search_metadata"]["total_results"],
            related_themes=None,  # Could be enhanced with theme extraction
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": str(e),
            },
        )
