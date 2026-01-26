"""Metadata API router for translations and books."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Book, Translation, Verse, get_db
from schemas import BookInfo, BooksResponse, TranslationInfo, TranslationsResponse

router = APIRouter(prefix="/api", tags=["metadata"])

# Language name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "ko": "한국어",
    "he": "Hebrew",
    "gr": "Greek",
}


@router.get("/translations", response_model=TranslationsResponse)
async def list_translations(
    language: Optional[str] = Query(
        None,
        description="Filter by language code (en, ko, he, gr)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all available Bible translations.

    Returns metadata for all translations, optionally filtered by language.
    """
    query = select(Translation)

    if language:
        query = query.where(Translation.language_code == language)

    translations = (await db.execute(query.order_by(Translation.language_code, Translation.name))).scalars().all()

    # Get verse counts for each translation
    verse_counts = dict(
        (await db.execute(
            select(Verse.translation_id, func.count(Verse.id))
            .group_by(Verse.translation_id)
        )).all()
    )

    result = []
    for trans in translations:
        result.append(
            TranslationInfo(
                id=trans.id,
                name=trans.name,
                abbreviation=trans.abbreviation,
                language_code=trans.language_code,
                language_name=LANGUAGE_NAMES.get(trans.language_code, trans.language_code),
                description=trans.description,
                is_original_language=trans.is_original_language,
                verse_count=verse_counts.get(trans.id, 0),
            )
        )

    return TranslationsResponse(
        translations=result,
        total_count=len(result),
    )


@router.get("/books", response_model=BooksResponse)
async def list_books(
    testament: Optional[str] = Query(
        None,
        description="Filter by testament: OT or NT",
        pattern="^(OT|NT)$",
    ),
    genre: Optional[str] = Query(
        None,
        description="Filter by genre",
    ),
    db: AsyncSession = Depends(get_db),
):
    """List all Bible books with metadata.

    Returns metadata for all 66 books, optionally filtered by
    testament or genre.
    """
    query = select(Book)

    if testament:
        query = query.where(Book.testament == testament)

    if genre:
        query = query.where(Book.genre == genre)

    books = (await db.execute(query.order_by(Book.book_number))).scalars().all()

    # Get verse counts for each book (using first translation)
    first_translation = (await db.execute(select(Translation).limit(1))).scalar_one_or_none()
    verse_counts = {}

    if first_translation:
        verse_counts = dict(
            (await db.execute(
                select(Verse.book_id, func.count(Verse.id))
                .where(Verse.translation_id == first_translation.id)
                .group_by(Verse.book_id)
            )).all()
        )

    result = []
    for book in books:
        result.append(
            BookInfo(
                id=book.id,
                name=book.name,
                name_korean=book.name_korean,
                abbreviation=book.abbreviation,
                testament=book.testament,
                genre=book.genre,
                book_number=book.book_number,
                total_chapters=book.total_chapters,
                total_verses=verse_counts.get(book.id, 0),
            )
        )

    return BooksResponse(
        books=result,
        total_count=len(result),
    )
