"""Metadata API router for translations and books."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

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
def list_translations(
    language: Optional[str] = Query(
        None,
        description="Filter by language code (en, ko, he, gr)",
    ),
    db: Session = Depends(get_db),
):
    """List all available Bible translations.

    Returns metadata for all translations, optionally filtered by language.
    """
    query = db.query(Translation)

    if language:
        query = query.filter(Translation.language_code == language)

    translations = query.order_by(Translation.language_code, Translation.name).all()

    # Get verse counts for each translation
    verse_counts = dict(
        db.query(Verse.translation_id, func.count(Verse.id))
        .group_by(Verse.translation_id)
        .all()
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
def list_books(
    testament: Optional[str] = Query(
        None,
        description="Filter by testament: OT or NT",
        pattern="^(OT|NT)$",
    ),
    genre: Optional[str] = Query(
        None,
        description="Filter by genre",
    ),
    db: Session = Depends(get_db),
):
    """List all Bible books with metadata.

    Returns metadata for all 66 books, optionally filtered by
    testament or genre.
    """
    query = db.query(Book)

    if testament:
        query = query.filter(Book.testament == testament)

    if genre:
        query = query.filter(Book.genre == genre)

    books = query.order_by(Book.book_number).all()

    # Get verse counts for each book (using first translation)
    first_translation = db.query(Translation).first()
    verse_counts = {}

    if first_translation:
        verse_counts = dict(
            db.query(Verse.book_id, func.count(Verse.id))
            .filter(Verse.translation_id == first_translation.id)
            .group_by(Verse.book_id)
            .all()
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
