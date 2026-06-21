"""Semantic search implementation for Bible RAG.

This module provides vector similarity search across Bible verses
with support for filtering by translation, testament, and genre.
Enhanced with hybrid search (vector + full-text), RRF fusion, and
query expansion support for improved retrieval quality.
"""

import logging
import time
from typing import Optional
from uuid import UUID

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PGUUID
from sqlalchemy import bindparam, Integer, Float

from cache import get_cache
from config import get_settings
from database import Book, CrossReference, Embedding, OriginalWord, Translation, Verse
from embeddings import embed_query, embed_query_async

settings = get_settings()
logger = logging.getLogger(__name__)

# Cached at startup by main.py lifespan to avoid a COUNT(*) on every request.
# None means unknown (startup check failed); will fall back to per-request check.
_has_embeddings: bool | None = None


async def fulltext_search_verses(
    db: AsyncSession,
    query: str,
    translation_ids: list,
    translation_map: dict,
    max_results: int,
    filters: Optional[dict],
    include_original: bool,
    include_cross_refs: bool,
    use_cache: bool,
    cache_key: str,
    start_time: float,
) -> dict:
    """Fallback full-text search when embeddings are not available.

    Uses PostgreSQL full-text search with ranking.

    Args:
        db: Database session
        query: Search query text
        translation_ids: List of translation UUIDs
        translation_map: Mapping of translation IDs to abbreviations
        max_results: Maximum number of results
        filters: Optional filters (testament, genre, books)
        include_original: Include original language data
        include_cross_refs: Include cross-references
        use_cache: Whether to use caching
        cache_key: Cache key for results
        start_time: Start time for query timing

    Returns:
        Dictionary with search results and metadata
    """
    from cache import get_cache

    cache = get_cache()

    bindparams_list = [
        bindparam("translation_ids", value=translation_ids, type_=ARRAY(PGUUID)),
        bindparam("max_results", value=max_results, type_=Integer),
    ]

    if _is_korean(query):
        sql_template = """
            WITH ranked_verses AS (
                SELECT DISTINCT ON (v.book_id, v.chapter, v.verse)
                    v.id as verse_id,
                    v.book_id,
                    v.chapter,
                    v.verse,
                    v.text,
                    v.translation_id,
                    b.name as book_name,
                    b.name_korean as book_name_korean,
                    b.abbreviation as book_abbrev,
                    b.testament,
                    b.genre,
                    word_similarity(:search_query, v.text) as rank
                FROM verses v
                JOIN books b ON v.book_id = b.id
                WHERE v.translation_id = ANY(:translation_ids)
                    AND word_similarity(:search_query, v.text) > 0.1
        """
        bindparams_list.append(bindparam("search_query", value=query))
    else:
        stopwords = {
            'what', 'does', 'the', 'bible', 'say', 'about', 'teach', 'us', 'tell',
            'me', 'can', 'you', 'how', 'why', 'when', 'where', 'who', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'did',
            'will', 'would', 'should', 'could', 'may', 'might', 'must', 'in', 'on',
            'at', 'to', 'for', 'of', 'with', 'from', 'by', 'as', 'that', 'this',
            'these', 'those', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'so', 'than',
        }
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        search_query = ' '.join(keywords) if keywords else query

        sql_template = """
            WITH ranked_verses AS (
                SELECT DISTINCT ON (v.book_id, v.chapter, v.verse)
                    v.id as verse_id,
                    v.book_id,
                    v.chapter,
                    v.verse,
                    v.text,
                    v.translation_id,
                    b.name as book_name,
                    b.name_korean as book_name_korean,
                    b.abbreviation as book_abbrev,
                    b.testament,
                    b.genre,
                    ts_rank_cd(to_tsvector('english', v.text), websearch_to_tsquery('english', :search_query)) as rank
                FROM verses v
                JOIN books b ON v.book_id = b.id
                WHERE v.translation_id = ANY(:translation_ids)
                    AND (
                        to_tsvector('english', v.text) @@ websearch_to_tsquery('english', :search_query)
                        OR v.text ILIKE '%' || :query_like || '%'
                    )
        """
        bindparams_list.append(bindparam("search_query", value=search_query))
        bindparams_list.append(bindparam("query_like", value=search_query))

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

    sql_template += """
            ORDER BY v.book_id, v.chapter, v.verse, rank DESC
        )
        SELECT *
        FROM ranked_verses
        WHERE rank > 0
        ORDER BY rank DESC
        LIMIT :max_results
    """

    # Execute query
    stmt = text(sql_template).bindparams(*bindparams_list)
    result = await db.execute(stmt)
    rows = result.fetchall()

    # Group results by verse reference
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
                "relevance_score": float(row.rank),
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
            result_item["cross_references"] = await get_cross_references(db, verse_id)

        # Get original language data
        if include_original:
            result_item["original"] = await get_original_words(db, verse_id)

    query_time_ms = int((time.time() - start_time) * 1000)

    response = {
        "query_time_ms": query_time_ms,
        "results": results,
        "search_metadata": {
            "total_results": len(results),
            "embedding_model": None,
            "search_method": "full-text",
            "cached": False,
        },
    }

    # Cache results
    if use_cache:
        cache.cache_results(cache_key, response, query)

    return response


async def get_chapter_by_reference(
    db: AsyncSession,
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
        await db.execute(
            select(Book)
            .where(
                (Book.name.ilike(book))
                | (Book.name_korean == book)
                | (Book.abbreviation.ilike(book))
            )
        )
    ).scalar_one_or_none()

    if not book_obj:
        return None

    # Build verse query for all verses in the chapter
    query = (
        select(Verse, Translation)
        .join(Translation)
        .where(
            Verse.book_id == book_obj.id,
            Verse.chapter == chapter,
        )
        .order_by(Verse.verse)
    )

    if translations:
        query = query.where(Translation.abbreviation.in_(translations))

    results = (await db.execute(query)).all()

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
            original = await get_original_words(db, UUID(verse_data["verse_id"]))
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


async def get_verse_by_reference(
    db: AsyncSession,
    book: str,
    chapter: int,
    verse: int,
    translations: Optional[list[str]] = None,
    include_original: bool = False,
    include_cross_refs: bool = True,
    use_cache: bool = True,
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
        use_cache: Whether to use caching

    Returns:
        Verse data dictionary or None if not found
    """
    cache = get_cache()

    # Generate cache key
    cache_key = cache.generate_verse_cache_key(
        book=book,
        chapter=chapter,
        verse=verse,
        translations=translations,
        include_original=include_original,
        include_cross_refs=include_cross_refs,
    )

    # Check cache
    if use_cache:
        cached = cache.get_cached_verse(cache_key)
        if cached:
            return cached

    # Find the book
    book_obj = (
        await db.execute(
            select(Book)
            .where(
                (Book.name.ilike(book))
                | (Book.name_korean == book)
                | (Book.abbreviation.ilike(book))
            )
        )
    ).scalar_one_or_none()

    if not book_obj:
        return None

    # Build verse query
    query = (
        select(Verse, Translation)
        .join(Translation)
        .where(
            Verse.book_id == book_obj.id,
            Verse.chapter == chapter,
            Verse.verse == verse,
        )
    )

    if translations:
        query = query.where(Translation.abbreviation.in_(translations))

    results = (await db.execute(query)).all()

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
        response["cross_references"] = await get_cross_references(db, first_verse.id)

    if include_original:
        response["original"] = await get_original_words(db, first_verse.id)

    # Get context (previous and next verses)
    response["context"] = await get_verse_context(db, book_obj.id, chapter, verse, translations or [])

    # Cache the result
    if use_cache:
        cache.cache_verse(cache_key, response)

    return response


async def get_verse_context(
    db: AsyncSession,
    book_id: UUID,
    chapter: int,
    verse: int,
    translation_abbrs: list[str] | None = None,
) -> dict:
    """Get surrounding context for a verse.

    Args:
        db: Database session
        book_id: Book ID
        chapter: Chapter number
        verse: Verse number
        translation_abbrs: Translation abbreviations to include (uses first available if empty)

    Returns:
        Dictionary with previous and next verse info, each with a translations dict
    """
    context: dict = {"previous": None, "next": None}

    # Convert UUID to string for SQLite compatibility in tests
    book_id_value = str(book_id) if isinstance(book_id, UUID) else book_id

    # Fetch context verses for all requested translations in one query
    query = (
        select(Verse, Translation)
        .join(Translation)
        .where(
            Verse.book_id == book_id_value,
            Verse.chapter == chapter,
            Verse.verse.in_([verse - 1, verse + 1]),
        )
    )

    if translation_abbrs:
        query = query.where(Translation.abbreviation.in_(translation_abbrs))

    rows = (await db.execute(query)).all()

    if not rows:
        return context

    # Group by verse number
    grouped: dict[int, dict] = {}
    for v, trans in rows:
        if v.verse not in grouped:
            grouped[v.verse] = {"chapter": v.chapter, "verse": v.verse, "translations": {}}
        grouped[v.verse]["translations"][trans.abbreviation] = (
            v.text[:100] + "..." if len(v.text) > 100 else v.text
        )

    if verse - 1 in grouped:
        context["previous"] = grouped[verse - 1]
    if verse + 1 in grouped:
        context["next"] = grouped[verse + 1]

    return context


async def search_by_theme(
    db: AsyncSession,
    theme: str,
    translations: list[str],
    testament: Optional[str] = None,
    max_results: int = 20,
    api_key: str | None = None,
) -> dict:
    """Search for verses by theme.

    This is essentially semantic search with testament filtering.

    Args:
        db: Database session
        theme: Theme keyword or phrase
        translations: List of translation abbreviations
        testament: Optional testament filter ('OT' or 'NT')
        max_results: Maximum number of results
        api_key: API key for embeddings

    Returns:
        Dictionary with search results
    """
    filters = {}
    if testament and testament != "both":
        filters["testament"] = testament

    results = await search_verses(
        db=db,
        query=theme,
        translations=translations,
        max_results=max_results,
        filters=filters,
        include_original=False,
        include_cross_refs=False,  # Don't include cross-refs for theme search to keep it clean
        api_key=api_key,
    )

    # Add theme-specific metadata
    results["theme"] = theme
    results["testament_filter"] = testament

    return results


def rrf_merge(
    ranked_lists: list[tuple[list[tuple[str, float]], float]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Merge multiple ranked lists using Weighted Reciprocal Rank Fusion.

    Args:
        ranked_lists: List of (ranked_results, weight) pairs where each
                      ranked_results is [(ref_key, score), ...] sorted desc.
                      weight amplifies contribution from high-quality sources
                      (e.g. main query = 2.0, expanded queries = 1.0).
        k: Smoothing constant (default 60, standard in literature).

    Returns:
        Merged list of (ref_key, rrf_score) sorted by RRF score descending.
    """
    scores: dict[str, float] = {}
    for ranked_list, weight in ranked_lists:
        for rank, (ref_key, _score) in enumerate(ranked_list):
            scores[ref_key] = scores.get(ref_key, 0.0) + weight / (rank + k)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


async def _vector_search(
    db: AsyncSession,
    query_embedding,
    translation_ids: list,
    filters: Optional[dict],
    similarity_threshold: float,
    limit: int,
) -> list[tuple[str, float, dict]]:
    """Run vector similarity search.

    Returns:
        List of (ref_key, similarity, row_data) tuples sorted by similarity desc.
    """
    query_vector_str = str(query_embedding.tolist())

    await db.execute(text("SET ivfflat.probes = 20"))

    sql_template = f"""
        WITH top_verses AS (
            SELECT DISTINCT ON (v.book_id, v.chapter, v.verse)
                v.id as verse_id,
                v.book_id,
                v.chapter,
                v.verse,
                v.text,
                v.translation_id,
                1 - (e.vector <=> '{query_vector_str}'::vector) as similarity,
                b.name as book_name,
                b.name_korean as book_name_korean,
                b.abbreviation as book_abbrev,
                b.testament,
                b.genre
            FROM embeddings e
            JOIN verses v ON e.verse_id = v.id
            JOIN books b ON v.book_id = b.id
            WHERE v.translation_id = ANY(:translation_ids)
                AND (1 - (e.vector <=> '{query_vector_str}'::vector)) > :similarity_threshold
    """

    bindparams_list = [
        bindparam("translation_ids", value=translation_ids, type_=ARRAY(PGUUID)),
        bindparam("similarity_threshold", value=similarity_threshold, type_=Float),
        bindparam("limit", value=limit, type_=Integer),
    ]

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

    sql_template += """
            ORDER BY v.book_id, v.chapter, v.verse, similarity DESC
        )
        SELECT * FROM top_verses
        ORDER BY similarity DESC
        LIMIT :limit
    """

    stmt = text(sql_template).bindparams(*bindparams_list)
    result = await db.execute(stmt)
    rows = result.fetchall()

    results = []
    for row in rows:
        ref_key = f"{row.book_id}:{row.chapter}:{row.verse}"
        row_data = {
            "verse_id": str(row.verse_id),
            "book_id": row.book_id,
            "chapter": row.chapter,
            "verse": row.verse,
            "text": row.text,
            "translation_id": row.translation_id,
            "similarity": row.similarity,
            "book_name": row.book_name,
            "book_name_korean": row.book_name_korean,
            "book_abbrev": row.book_abbrev,
            "testament": row.testament,
            "genre": row.genre,
        }
        results.append((ref_key, float(row.similarity), row_data))
    return results


def _is_korean(text: str) -> bool:
    """Return True if text contains a meaningful proportion of Korean (Hangul) characters."""
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return False
    korean = sum(1 for c in alpha if "가" <= c <= "힣" or "ㄱ" <= c <= "ㅣ")
    return korean / len(alpha) > 0.3


async def _fulltext_search(
    db: AsyncSession,
    query: str,
    translation_ids: list,
    filters: Optional[dict],
    limit: int,
) -> list[tuple[str, float, dict]]:
    """Run PostgreSQL full-text search.

    For English queries: uses websearch_to_tsquery with ts_rank_cd (cover density).
    For Korean queries: uses pg_trgm word_similarity() since to_tsvector('english')
    cannot tokenize Hangul — Korean verses return zero results from tsvector.

    Returns:
        List of (ref_key, rank, row_data) tuples sorted by rank desc.
    """
    bindparams_list = [
        bindparam("translation_ids", value=translation_ids, type_=ARRAY(PGUUID)),
        bindparam("limit", value=limit, type_=Integer),
    ]

    if _is_korean(query):
        # pg_trgm word_similarity: score in [0,1], works for any script.
        # We require at least 0.1 to filter noise; rank directly by similarity.
        sql_template = """
            WITH ranked_verses AS (
                SELECT DISTINCT ON (v.book_id, v.chapter, v.verse)
                    v.id as verse_id,
                    v.book_id,
                    v.chapter,
                    v.verse,
                    v.text,
                    v.translation_id,
                    b.name as book_name,
                    b.name_korean as book_name_korean,
                    b.abbreviation as book_abbrev,
                    b.testament,
                    b.genre,
                    word_similarity(:search_query, v.text) as rank
                FROM verses v
                JOIN books b ON v.book_id = b.id
                WHERE v.translation_id = ANY(:translation_ids)
                    AND word_similarity(:search_query, v.text) > 0.1
        """
        bindparams_list.append(bindparam("search_query", value=query))
    else:
        # English: strip stopwords, use websearch_to_tsquery with cover-density rank.
        stopwords = {
            'what', 'does', 'the', 'bible', 'say', 'about', 'teach', 'us', 'tell',
            'me', 'can', 'you', 'how', 'why', 'when', 'where', 'who', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'did',
            'will', 'would', 'should', 'could', 'may', 'might', 'must', 'in', 'on',
            'at', 'to', 'for', 'of', 'with', 'from', 'by', 'as', 'that', 'this',
            'these', 'those', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'so', 'than',
        }
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        search_query = ' '.join(keywords) if keywords else query

        sql_template = """
            WITH ranked_verses AS (
                SELECT DISTINCT ON (v.book_id, v.chapter, v.verse)
                    v.id as verse_id,
                    v.book_id,
                    v.chapter,
                    v.verse,
                    v.text,
                    v.translation_id,
                    b.name as book_name,
                    b.name_korean as book_name_korean,
                    b.abbreviation as book_abbrev,
                    b.testament,
                    b.genre,
                    ts_rank_cd(to_tsvector('english', v.text), websearch_to_tsquery('english', :search_query)) as rank
                FROM verses v
                JOIN books b ON v.book_id = b.id
                WHERE v.translation_id = ANY(:translation_ids)
                    AND (
                        to_tsvector('english', v.text) @@ websearch_to_tsquery('english', :search_query)
                        OR v.text ILIKE '%' || :query_like || '%'
                    )
        """
        bindparams_list.append(bindparam("search_query", value=search_query))
        bindparams_list.append(bindparam("query_like", value=search_query))

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

    sql_template += """
            ORDER BY v.book_id, v.chapter, v.verse, rank DESC
        )
        SELECT *
        FROM ranked_verses
        WHERE rank > 0
        ORDER BY rank DESC
        LIMIT :limit
    """

    stmt = text(sql_template).bindparams(*bindparams_list)
    result = await db.execute(stmt)
    rows = result.fetchall()

    results = []
    for row in rows:
        ref_key = f"{row.book_id}:{row.chapter}:{row.verse}"
        row_data = {
            "verse_id": str(row.verse_id),
            "book_id": row.book_id,
            "chapter": row.chapter,
            "verse": row.verse,
            "text": row.text,
            "translation_id": row.translation_id,
            "similarity": float(row.rank),
            "book_name": row.book_name,
            "book_name_korean": row.book_name_korean,
            "book_abbrev": row.book_abbrev,
            "testament": row.testament,
            "genre": row.genre,
        }
        results.append((ref_key, float(row.rank), row_data))
    return results


async def search_verses(
    db: AsyncSession,
    query: str,
    translations: list[str],
    max_results: int = 10,
    filters: Optional[dict] = None,
    include_original: bool = False,
    include_cross_refs: bool = True,
    use_cache: bool = True,
    api_key: str | None = None,
    expanded_queries: list[str] | None = None,
) -> dict:
    """Perform enhanced semantic search across Bible verses.

    Uses hybrid search (vector + full-text) with RRF fusion and
    optional query expansion for improved retrieval quality.

    Args:
        db: Database session
        query: Search query text
        translations: List of translation abbreviations to search
        max_results: Maximum number of results to return
        filters: Optional filters (testament, genre, books)
        include_original: Include original language data
        include_cross_refs: Include cross-references
        use_cache: Whether to use caching
        api_key: Gemini API key (required if EMBEDDING_MODE=gemini)
        expanded_queries: Additional search queries from query expansion

    Returns:
        Dictionary with search results and metadata
    """
    start_time = time.time()
    cache = get_cache()

    # Generate cache key (include expanded queries for cache differentiation)
    cache_key = cache.generate_cache_key(query, translations, filters)

    # Check cache
    if use_cache:
        cached = cache.get_cached_results(cache_key)
        if cached:
            cached["cached"] = True
            return cached

    # Get translation IDs
    translation_objs = (
        await db.execute(
            select(Translation)
            .where(Translation.abbreviation.in_(translations))
        )
    ).scalars().all()
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

    # Check if embeddings table has data (use cached value from startup when available)
    if _has_embeddings is None:
        embeddings_count = (await db.execute(select(func.count()).select_from(Embedding))).scalar()
        has_embeddings = (embeddings_count or 0) > 0
    else:
        has_embeddings = _has_embeddings

    # Use full-text search if no embeddings available
    if not has_embeddings:
        return await fulltext_search_verses(
            db=db,
            query=query,
            translation_ids=translation_ids,
            translation_map=translation_map,
            max_results=max_results,
            filters=filters,
            include_original=include_original,
            include_cross_refs=include_cross_refs,
            use_cache=use_cache,
            cache_key=cache_key,
            start_time=start_time,
        )

    # --- Enhanced retrieval pipeline ---
    import asyncio

    internal_limit = max_results * settings.overretrieve_factor
    # ranked_lists holds (ranked_list, weight) pairs for weighted RRF.
    # Main query gets weight 2.0; expanded queries get weight 1.0.
    ranked_lists_weighted: list[tuple[list[tuple[str, float]], float]] = []
    # Store row data keyed by ref_key for later assembly
    all_row_data: dict[str, dict] = {}

    # 1 & 3. Embed main query + all expanded queries concurrently (non-blocking)
    all_queries = [query] + (expanded_queries or [])
    embeddings = await asyncio.gather(
        *[embed_query_async(q, api_key=api_key) for q in all_queries],
        return_exceptions=True,
    )
    query_embedding = embeddings[0] if not isinstance(embeddings[0], Exception) else None

    if query_embedding is None:
        logger.error(f"Failed to embed main query: {embeddings[0]}")
        return {
            "query_time_ms": int((time.time() - start_time) * 1000),
            "results": [],
            "search_metadata": {"total_results": 0, "error": "Embedding failed"},
        }

    # 1. Vector search on main query (weight=2.0 — higher signal than expansions)
    vector_results = await _vector_search(
        db, query_embedding, translation_ids, filters,
        settings.similarity_threshold, internal_limit,
    )
    if vector_results:
        ranked_lists_weighted.append(([(ref, score) for ref, score, _ in vector_results], 2.0))
        for ref, _score, row_data in vector_results:
            all_row_data[ref] = row_data

    # 2. Full-text search on original query (hybrid, weight=2.0)
    if settings.enable_hybrid_search:
        ft_results = await _fulltext_search(
            db, query, translation_ids, filters, internal_limit,
        )
        if ft_results:
            ranked_lists_weighted.append(([(ref, score) for ref, score, _ in ft_results], 2.0))
            for ref, _score, row_data in ft_results:
                if ref not in all_row_data:
                    all_row_data[ref] = row_data

    # 3. Vector search on expanded queries (weight=1.0 — supporting signal)
    if expanded_queries:
        eq_embeddings = embeddings[1:]
        for eq, eq_embedding in zip(expanded_queries, eq_embeddings):
            if isinstance(eq_embedding, Exception):
                logger.warning(f"Expanded query embedding failed for {eq!r}: {eq_embedding}")
                continue
            try:
                eq_results = await _vector_search(
                    db, eq_embedding, translation_ids, filters,
                    settings.similarity_threshold, internal_limit,
                )
                if eq_results:
                    ranked_lists_weighted.append(
                        ([(ref, score) for ref, score, _ in eq_results], 1.0)
                    )
                    for ref, _score, row_data in eq_results:
                        if ref not in all_row_data:
                            all_row_data[ref] = row_data
            except Exception as e:
                logger.warning(f"Expanded query search failed for {eq!r}: {e}")

    # 4. Weighted RRF merge all ranked lists
    if len(ranked_lists_weighted) > 1:
        merged = rrf_merge(ranked_lists_weighted, k=settings.rrf_k)
        search_method = "hybrid-rrf"
    elif ranked_lists_weighted:
        merged = ranked_lists_weighted[0][0]
        search_method = "semantic"
    else:
        merged = []
        search_method = "none"

    # 4b. Cross-encoder reranking
    if settings.enable_reranking and merged:
        from reranker import rerank

        rerank_count = min(len(merged), settings.rerank_top_n)
        candidates = []
        for ref_key, rrf_score in merged[:rerank_count]:
            row_data = all_row_data.get(ref_key)
            if row_data:
                candidates.append({
                    "ref_key": ref_key,
                    "text": row_data["text"],
                    "rrf_score": rrf_score,
                })

        if candidates:
            try:
                reranked = rerank(query, candidates, top_k=max_results)
                top_refs = [(c["ref_key"], c["rerank_score"]) for c in reranked]
                search_method += "+rerank"
            except Exception as e:
                logger.warning(f"Reranking failed, falling back to RRF order: {e}")
                top_refs = merged[:max_results]
        else:
            top_refs = merged[:max_results]
    else:
        top_refs = merged[:max_results]

    # 5. Assemble results with translation grouping
    # Need to fetch all translations for the selected verses
    verse_groups = {}
    for ref_key, rrf_score in top_refs:
        row_data = all_row_data.get(ref_key)
        if not row_data:
            continue
        verse_groups[ref_key] = {
            "reference": {
                "book": row_data["book_name"],
                "book_korean": row_data["book_name_korean"],
                "book_abbrev": row_data["book_abbrev"],
                "chapter": row_data["chapter"],
                "verse": row_data["verse"],
                "testament": row_data["testament"],
                "genre": row_data["genre"],
            },
            "translations": {},
            "relevance_score": rrf_score,
            "verse_id": row_data["verse_id"],
        }
        trans_abbrev = translation_map.get(str(row_data["translation_id"]), "Unknown")
        verse_groups[ref_key]["translations"][trans_abbrev] = row_data["text"]

    # Fetch additional translations for each result
    for ref_key, group in verse_groups.items():
        row_data = all_row_data[ref_key]
        extra_verses = (
            await db.execute(
                select(Verse, Translation)
                .join(Translation)
                .where(
                    Verse.book_id == row_data["book_id"],
                    Verse.chapter == row_data["chapter"],
                    Verse.verse == row_data["verse"],
                    Verse.translation_id.in_(translation_ids),
                )
            )
        ).all()
        for v, t in extra_verses:
            group["translations"][t.abbreviation] = v.text
            if not group.get("verse_id"):
                group["verse_id"] = str(v.id)

    # Maintain order from RRF ranking
    results = [verse_groups[ref] for ref, _ in top_refs if ref in verse_groups]

    # 5b. Fill single-verse gaps in consecutive chapter sequences
    results = await _fill_verse_gaps(db, results, translation_ids, translation_map)

    # 6. Fetch enrichment data
    for result_item in results:
        verse_id = UUID(result_item["verse_id"])
        if include_cross_refs:
            result_item["cross_references"] = await get_cross_references(db, verse_id)
        if include_original:
            result_item["original"] = await get_original_words(db, verse_id)

    query_time_ms = int((time.time() - start_time) * 1000)

    expanded_count = len(expanded_queries) if expanded_queries else 0
    response = {
        "query_time_ms": query_time_ms,
        "results": results,
        "search_metadata": {
            "total_results": len(results),
            "embedding_model": settings.embedding_model,
            "search_method": search_method,
            "expanded_queries": expanded_queries or [],
            "cached": False,
        },
    }

    # Cache results
    if use_cache:
        cache.cache_results(cache_key, response, query)

    return response


async def _fill_verse_gaps(
    db: AsyncSession,
    results: list[dict],
    translation_ids: list,
    translation_map: dict,
) -> list[dict]:
    """Insert missing verses that fall between consecutive retrieved verses in the same chapter.

    When the result set contains verse N and verse N+2 from the same book and
    chapter, verse N+1 is fetched and inserted between them. This prevents the
    LLM from missing critical context — e.g., receiving Mark 12:29 and 12:31
    without 12:30, which contains the actual commandment text.

    Only fills single-verse gaps (gap of exactly 1) to avoid over-fetching.
    Gap-filled verses are marked with gap_fill=True so the frontend can
    optionally style them differently.
    """
    if len(results) < 2:
        return results

    from collections import defaultdict

    # Map each (book, chapter) to the list of (verse_num, result_index) present
    chapter_groups: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    for i, result in enumerate(results):
        ref = result.get("reference", {})
        book = ref.get("book", "")
        chapter = ref.get("chapter")
        verse = ref.get("verse")
        if book and chapter is not None and verse is not None:
            chapter_groups[(book, chapter)].append((verse, i))

    # Find gaps of exactly 1 verse within each chapter group
    gaps: list[tuple] = []  # (book, chapter, gap_verse, insert_after_idx, avg_score)
    for (book, chapter), verse_indices in chapter_groups.items():
        if len(verse_indices) < 2:
            continue
        sorted_pairs = sorted(verse_indices)  # sort by verse_num ascending
        for j in range(len(sorted_pairs) - 1):
            curr_verse, curr_idx = sorted_pairs[j]
            nxt_verse, nxt_idx = sorted_pairs[j + 1]
            if nxt_verse - curr_verse == 2:
                avg_score = (
                    results[curr_idx].get("relevance_score", 0)
                    + results[nxt_idx].get("relevance_score", 0)
                ) / 2 * 0.9
                gaps.append((book, chapter, curr_verse + 1, curr_idx, avg_score))

    if not gaps:
        return results

    # Track already-present verses to avoid duplicate inserts
    present: set[tuple] = {
        (r["reference"]["book"], r["reference"]["chapter"], r["reference"]["verse"])
        for r in results
        if r.get("reference")
    }

    filled = list(results)
    # Insert in descending order of insert_after_idx so earlier indices stay valid
    for book, chapter, gap_verse, insert_after_idx, avg_score in sorted(
        gaps, key=lambda x: x[3], reverse=True
    ):
        if (book, chapter, gap_verse) in present:
            continue

        gap_rows = (
            await db.execute(
                select(Verse, Translation, Book)
                .join(Translation, Verse.translation_id == Translation.id)
                .join(Book, Verse.book_id == Book.id)
                .where(
                    Book.name == book,
                    Verse.chapter == chapter,
                    Verse.verse == gap_verse,
                    Verse.translation_id.in_(translation_ids),
                )
            )
        ).all()

        if not gap_rows:
            continue

        first_verse, _, first_book = gap_rows[0]
        gap_result = {
            "reference": {
                "book": first_book.name,
                "book_korean": first_book.name_korean,
                "book_abbrev": first_book.abbreviation,
                "chapter": chapter,
                "verse": gap_verse,
                "testament": first_book.testament,
                "genre": first_book.genre,
            },
            "translations": {
                translation_map.get(str(v.translation_id), "Unknown"): v.text
                for v, t, b in gap_rows
            },
            "relevance_score": avg_score,
            "verse_id": str(first_verse.id),
            "gap_fill": True,
        }

        filled.insert(insert_after_idx + 1, gap_result)
        present.add((book, chapter, gap_verse))
        logger.info(f"Gap-filled: {book} {chapter}:{gap_verse}")

    return filled


async def get_cross_references(db: AsyncSession, verse_id: UUID, limit: int = 5) -> list[dict]:
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
        await db.execute(
            select(CrossReference, Verse, Book)
            .join(Verse, CrossReference.related_verse_id == Verse.id)
            .join(Book, Verse.book_id == Book.id)
            .where(CrossReference.verse_id == verse_id_value)
            .order_by(CrossReference.confidence.desc())
            .limit(limit)
        )
    ).all()

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


async def get_original_words(db: AsyncSession, verse_id: UUID) -> Optional[dict]:
    """Get original language words for a verse.

    Args:
        db: Database session
        verse_id: ID of the verse

    Returns:
        Dictionary with original language data or None
    """
    # Convert UUID to string for SQLite compatibility in tests
    verse_id_value = str(verse_id) if isinstance(verse_id, UUID) else verse_id

    # First try direct lookup
    words = (
        await db.execute(
            select(OriginalWord)
            .where(OriginalWord.verse_id == verse_id_value)
            .order_by(OriginalWord.word_order)
        )
    ).scalars().all()

    # If no words found, look up by book/chapter/verse reference
    if not words:
        # Get the verse reference
        verse = (await db.execute(select(Verse).where(Verse.id == verse_id_value))).scalar_one_or_none()
        if verse:
            # Find any verse with the same book/chapter/verse that has original words
            sibling_verses = (
                await db.execute(
                    select(Verse)
                    .where(
                        Verse.book_id == verse.book_id,
                        Verse.chapter == verse.chapter,
                        Verse.verse == verse.verse,
                    )
                )
            ).scalars().all()

            for sibling in sibling_verses:
                words = (
                    await db.execute(
                        select(OriginalWord)
                        .where(OriginalWord.verse_id == sibling.id)
                        .order_by(OriginalWord.word_order)
                    )
                ).scalars().all()
                if words:
                    break

    if not words:
        return None

    # Determine language from first word
    language = words[0].language if words else None

    # Build full text from words
    text = " ".join([w.word for w in words])

    # Build full transliteration from words
    transliteration = " ".join([w.transliteration for w in words if w.transliteration])

    # Collect unique Strong's numbers
    strongs = list(set([w.strongs_number for w in words if w.strongs_number]))

    return {
        "language": language,
        "text": text,
        "transliteration": transliteration if transliteration else None,
        "strongs": strongs,
        "words": [
            {
                "word": w.word,
                "transliteration": w.transliteration,
                "strongs": w.strongs_number,
                "morphology": w.morphology,
                "definition": w.definition,
                "word_order": w.word_order,
            }
            for w in words
        ],
    }
