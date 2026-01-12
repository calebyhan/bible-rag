"""Verses API router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import VerseDetailResponse
from search import get_verse_by_reference

router = APIRouter(prefix="/api", tags=["verses"])


@router.get("/verse/{book}/{chapter}/{verse}", response_model=VerseDetailResponse)
def get_verse(
    book: str,
    chapter: int,
    verse: int,
    translations: Optional[str] = Query(
        None,
        description="Comma-separated translation abbreviations",
    ),
    include_original: bool = Query(
        False,
        description="Include original language data",
    ),
    include_cross_refs: bool = Query(
        True,
        description="Include cross-references",
    ),
    db: Session = Depends(get_db),
):
    """Get a specific verse by reference.

    Retrieve a verse in multiple translations with optional original
    language data and cross-references.

    Args:
        book: Book name or abbreviation (e.g., 'John', '요한복음', 'John')
        chapter: Chapter number
        verse: Verse number
        translations: Comma-separated translation abbreviations
        include_original: Include Greek/Hebrew data
        include_cross_refs: Include cross-references

    Returns:
        Verse data with translations and optional enrichments
    """
    # Parse translations
    translation_list = None
    if translations:
        translation_list = [t.strip() for t in translations.split(",")]

    result = get_verse_by_reference(
        db=db,
        book=book,
        chapter=chapter,
        verse=verse,
        translations=translation_list,
        include_original=include_original,
        include_cross_refs=include_cross_refs,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "VERSE_NOT_FOUND",
                "message": "Verse not found",
                "details": {
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                },
            },
        )

    return VerseDetailResponse(**result)
