"""Semantic search implementation for Bible RAG.

This module provides vector similarity search across Bible verses
with support for filtering by translation, testament, and genre.
"""

import time
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy import bindparam, Integer, Float

from cache import get_cache
from config import get_settings
from database import Book, CrossReference, Embedding, OriginalWord, Translation, Verse
from embeddings import embed_query

settings = get_settings()


def search_verses(
    db: Session,
    query: str,
    translations: list[str],
    max_results: int = 10,
    filters: Optional[dict] = None,
    include_original: bool = False,
    include_cross_refs: bool = True,
    use_cache: bool = True,
) -> dict:
    """Perform semantic search across Bible verses.

    Args:
        db: Database session
        query: Search query text
        translations: List of translation abbreviations to search
        max_results: Maximum number of results to return
        filters: Optional filters (testament, genre, books)
        include_original: Include original language data
        include_cross_refs: Include cross-references
        use_cache: Whether to use caching

    Returns:
        Dictionary with search results and metadata
    """
    start_time = time.time()
    cache = get_cache()

    # Generate cache key
    cache_key = cache.generate_cache_key(query, translations, filters)

    # Check cache
    if use_cache:
        cached = cache.get_cached_results(cache_key)
        if cached:
            cached["cached"] = True
            return cached

    # Get translation IDs
    translation_objs = (
        db.query(Translation)
        .filter(Translation.abbreviation.in_(translations))
        .all()
    )
    translation_ids = [t.id for t in translation_objs]
    translation_map = {str(t.id): t.abbreviation for t in translation_objs}

    if not translation_ids:
        return {
            "query_time_ms": int((time.time() - start_time) * 1000),
            "results": [],
            "search_metadata": {
                "total_results": 0,
                "error": "No valid translations found",
            },
        }

    # Generate query embedding
    query_embedding = embed_query(query)

    # Build the SQL query for vector similarity search
    # Using raw SQL for pgvector operations
    # Convert query_embedding to string format for PostgreSQL
    query_vector_str = str(query_embedding.tolist())

    # Set ivfflat probes for better accuracy (search more clusters)
    # Higher = more accurate but slower. Default is 1, we use 20 for better recall
    db.execute(text("SET ivfflat.probes = 20"))

    # Build SQL query - embed vector directly, use bindparams for UUIDs/scalars
    sql_template = f"""
        WITH verse_scores AS (
            SELECT
                v.id as verse_id,
                v.book_id,
                v.chapter,
                v.verse,
                v.text,
                v.translation_id,
                1 - (e.vector <=> '{query_vector_str}'::vector) as similarity
            FROM embeddings e
            JOIN verses v ON e.verse_id = v.id
            JOIN books b ON v.book_id = b.id
            WHERE v.translation_id = ANY(:translation_ids)
    """

    bindparams_list = [
        bindparam("translation_ids", value=translation_ids, type_=ARRAY(PGUUID)),
        bindparam("similarity_threshold", value=settings.similarity_threshold, type_=Float),
        bindparam("max_results", value=max_results, type_=Integer),
    ]

    # Apply filters
    if filters:
        if filters.get("testament"):
            sql_template += " AND b.testament = :testament"
            bindparams_list.append(bindparam("testament", value=filters["testament"]))

        if filters.get("genre"):
            sql_template += " AND b.genre = :genre"
            bindparams_list.append(bindparam("genre", value=filters["genre"]))

        if filters.get("books"):
            sql_template += " AND b.abbreviation = ANY(:book_abbrevs)"
            bindparams_list.append(
                bindparam("book_abbrevs", value=filters["books"], type_=ARRAY(PGUUID))
            )

    # Add similarity threshold and limit
    sql_template += f"""
            AND (1 - (e.vector <=> '{query_vector_str}'::vector)) > :similarity_threshold
            ORDER BY e.vector <=> '{query_vector_str}'::vector
            LIMIT :max_results
        )
        SELECT
            vs.verse_id,
            vs.book_id,
            vs.chapter,
            vs.verse,
            vs.text,
            vs.translation_id,
            vs.similarity,
            b.name as book_name,
            b.name_korean as book_name_korean,
            b.abbreviation as book_abbrev,
            b.testament,
            b.genre
        FROM verse_scores vs
        JOIN books b ON vs.book_id = b.id
        ORDER BY vs.similarity DESC
    """

    # Execute query with bindparams
    stmt = text(sql_template).bindparams(*bindparams_list)
    result = db.execute(stmt)
    rows = result.fetchall()

    # Group results by verse reference (book + chapter + verse)
    # to consolidate translations
    verse_groups = {}
    for row in rows:
        ref_key = f"{row.book_id}:{row.chapter}:{row.verse}"

        if ref_key not in verse_groups:
            verse_groups[ref_key] = {
                "reference": {
                    "book": row.book_name,
                    "book_korean": row.book_name_korean,
                    "book_abbrev": row.book_abbrev,
                    "chapter": row.chapter,
                    "verse": row.verse,
                    "testament": row.testament,
                    "genre": row.genre,
                },
                "translations": {},
                "relevance_score": row.similarity,
                "verse_id": str(row.verse_id),
            }

        trans_abbrev = translation_map.get(str(row.translation_id), "Unknown")
        verse_groups[ref_key]["translations"][trans_abbrev] = row.text

    # Convert to list
    results = list(verse_groups.values())

    # Fetch additional data if requested
    for result_item in results:
        verse_id = UUID(result_item["verse_id"])

        # Get cross-references
        if include_cross_refs:
            result_item["cross_references"] = get_cross_references(db, verse_id)

        # Get original language data
        if include_original:
            result_item["original"] = get_original_words(db, verse_id)

    query_time_ms = int((time.time() - start_time) * 1000)

    response = {
        "query_time_ms": query_time_ms,
        "results": results,
        "search_metadata": {
            "total_results": len(results),
            "embedding_model": settings.embedding_model,
            "cached": False,
        },
    }

    # Cache results
    if use_cache:
        cache.cache_results(cache_key, response, query)

    return response


def get_cross_references(db: Session, verse_id: UUID, limit: int = 5) -> list[dict]:
    """Get cross-references for a verse.

    Args:
        db: Database session
        verse_id: ID of the verse to get cross-references for
        limit: Maximum number of cross-references

    Returns:
        List of cross-reference dictionaries
    """
    # Convert UUID to string for SQLite compatibility in tests
    verse_id_value = str(verse_id) if isinstance(verse_id, UUID) else verse_id

    refs = (
        db.query(CrossReference, Verse, Book)
        .join(Verse, CrossReference.related_verse_id == Verse.id)
        .join(Book, Verse.book_id == Book.id)
        .filter(CrossReference.verse_id == verse_id_value)
        .order_by(CrossReference.confidence.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "book": book.name,
            "book_korean": book.name_korean,
            "chapter": verse.chapter,
            "verse": verse.verse,
            "relationship": cross_ref.relationship_type,
            "confidence": cross_ref.confidence,
        }
        for cross_ref, verse, book in refs
    ]


def get_original_words(db: Session, verse_id: UUID) -> Optional[dict]:
    """Get original language words for a verse.

    Args:
        db: Database session
        verse_id: ID of the verse

    Returns:
        Dictionary with original language data or None
    """
    # Convert UUID to string for SQLite compatibility in tests
    verse_id_value = str(verse_id) if isinstance(verse_id, UUID) else verse_id

    words = (
        db.query(OriginalWord)
        .filter(OriginalWord.verse_id == verse_id_value)
        .order_by(OriginalWord.word_order)
        .all()
    )

    if not words:
        return None

    # Determine language from first word
    language = words[0].language if words else None

    return {
        "language": language,
        "words": [
            {
                "word": w.word,
                "transliteration": w.transliteration,
                "strongs": w.strongs_number,
                "morphology": w.morphology,
                "definition": w.definition,
            }
            for w in words
        ],
    }


def get_chapter_by_reference(
    db: Session,
    book: str,
    chapter: int,
    translations: Optional[list[str]] = None,
    include_original: bool = False,
) -> Optional[dict]:
    """Get an entire chapter with all verses.

    Args:
        db: Database session
        book: Book name or abbreviation
        chapter: Chapter number
        translations: List of translation abbreviations (all if None)
        include_original: Include original language data

    Returns:
        Chapter data dictionary with all verses or None if not found
    """
    # Find the book
    book_obj = (
        db.query(Book)
        .filter(
            (Book.name.ilike(book))
            | (Book.name_korean == book)
            | (Book.abbreviation.ilike(book))
        )
        .first()
    )

    if not book_obj:
        return None

    # Build verse query for all verses in the chapter
    query = (
        db.query(Verse, Translation)
        .join(Translation)
        .filter(
            Verse.book_id == book_obj.id,
            Verse.chapter == chapter,
        )
        .order_by(Verse.verse)
    )

    if translations:
        query = query.filter(Translation.abbreviation.in_(translations))

    results = query.all()

    if not results:
        return None

    # Group verses by verse number
    verses_dict = {}
    for verse_obj, translation in results:
        verse_num = verse_obj.verse
        if verse_num not in verses_dict:
            verses_dict[verse_num] = {
                "verse_id": str(verse_obj.id),
                "verse": verse_num,
                "translations": {},
            }
        verses_dict[verse_num]["translations"][translation.abbreviation] = verse_obj.text

    # Convert to list and sort by verse number
    verses_list = [verses_dict[v] for v in sorted(verses_dict.keys())]

    # Add original language data if requested
    if include_original:
        for verse_data in verses_list:
            original = get_original_words(db, verse_data["verse_id"])
            if original:
                verse_data["original"] = original

    return {
        "reference": {
            "book": book_obj.name,
            "book_korean": book_obj.name_korean,
            "chapter": chapter,
            "testament": book_obj.testament,
        },
        "verses": verses_list,
    }


def get_verse_by_reference(
    db: Session,
    book: str,
    chapter: int,
    verse: int,
    translations: Optional[list[str]] = None,
    include_original: bool = False,
    include_cross_refs: bool = True,
) -> Optional[dict]:
    """Get a specific verse by reference.

    Args:
        db: Database session
        book: Book name or abbreviation
        chapter: Chapter number
        verse: Verse number
        translations: List of translation abbreviations (all if None)
        include_original: Include original language data
        include_cross_refs: Include cross-references

    Returns:
        Verse data dictionary or None if not found
    """
    # Find the book
    book_obj = (
        db.query(Book)
        .filter(
            (Book.name.ilike(book))
            | (Book.name_korean == book)
            | (Book.abbreviation.ilike(book))
        )
        .first()
    )

    if not book_obj:
        return None

    # Build verse query
    query = (
        db.query(Verse, Translation)
        .join(Translation)
        .filter(
            Verse.book_id == book_obj.id,
            Verse.chapter == chapter,
            Verse.verse == verse,
        )
    )

    if translations:
        query = query.filter(Translation.abbreviation.in_(translations))

    results = query.all()

    if not results:
        return None

    # Get first verse for cross-refs and original words
    first_verse = results[0][0]

    response = {
        "reference": {
            "book": book_obj.name,
            "book_korean": book_obj.name_korean,
            "chapter": chapter,
            "verse": verse,
            "testament": book_obj.testament,
            "genre": book_obj.genre,
        },
        "translations": {trans.abbreviation: v.text for v, trans in results},
    }

    if include_cross_refs:
        response["cross_references"] = get_cross_references(db, first_verse.id)

    if include_original:
        response["original"] = get_original_words(db, first_verse.id)

    # Get context (previous and next verses)
    response["context"] = get_verse_context(db, book_obj.id, chapter, verse)

    return response


def get_verse_context(
    db: Session,
    book_id: UUID,
    chapter: int,
    verse: int,
) -> dict:
    """Get surrounding context for a verse.

    Args:
        db: Database session
        book_id: Book ID
        chapter: Chapter number
        verse: Verse number

    Returns:
        Dictionary with previous and next verse info
    """
    context = {"previous": None, "next": None}

    # Convert UUID to string for SQLite compatibility in tests
    book_id_value = str(book_id) if isinstance(book_id, UUID) else book_id

    # Get one translation for context
    translation = db.query(Translation).first()
    if not translation:
        return context

    # Previous verse
    prev_verse = (
        db.query(Verse)
        .filter(
            Verse.book_id == book_id_value,
            Verse.translation_id == translation.id,
            Verse.chapter == chapter,
            Verse.verse == verse - 1,
        )
        .first()
    )

    if prev_verse:
        context["previous"] = {
            "chapter": prev_verse.chapter,
            "verse": prev_verse.verse,
            "text": prev_verse.text[:100] + "..." if len(prev_verse.text) > 100 else prev_verse.text,
        }

    # Next verse
    next_verse = (
        db.query(Verse)
        .filter(
            Verse.book_id == book_id_value,
            Verse.translation_id == translation.id,
            Verse.chapter == chapter,
            Verse.verse == verse + 1,
        )
        .first()
    )

    if next_verse:
        context["next"] = {
            "chapter": next_verse.chapter,
            "verse": next_verse.verse,
            "text": next_verse.text[:100] + "..." if len(next_verse.text) > 100 else next_verse.text,
        }

    return context


def search_by_theme(
    db: Session,
    theme: str,
    translations: list[str],
    testament: Optional[str] = None,
    max_results: int = 20,
) -> dict:
    """Search for verses by theme.

    This is essentially semantic search with testament filtering.

    Args:
        db: Database session
        theme: Theme keyword or phrase
        translations: List of translation abbreviations
        testament: Optional testament filter ('OT' or 'NT')
        max_results: Maximum results

    Returns:
        Search results dictionary
    """
    filters = {}
    if testament and testament != "both":
        filters["testament"] = testament

    results = search_verses(
        db=db,
        query=theme,
        translations=translations,
        max_results=max_results,
        filters=filters,
        include_original=False,
        include_cross_refs=True,
    )

    # Add theme-specific metadata
    results["theme"] = theme
    results["testament_filter"] = testament

    return results
