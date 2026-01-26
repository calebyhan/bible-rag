"""Tests for search functionality."""

import pytest
import uuid
from unittest.mock import patch, MagicMock
import numpy as np

@pytest.mark.asyncio
@pytest.mark.unit
async def test_search_verses_no_translations(test_db):
    """Test search with invalid translations returns empty results."""
    from search import search_verses

    with patch("search.embed_query") as mock_embed:
        mock_embed.return_value = np.array([0.1] * 1024)

        results = await search_verses(
            db=test_db,
            query="test query",
            translations=["INVALID"],
            max_results=10,
            use_cache=False,
        )

        assert results["search_metadata"]["total_results"] == 0
        assert "error" in results["search_metadata"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_cross_references_empty(test_db, sample_verse):
    """Test getting cross-references for verse with none."""
    from search import get_cross_references

    refs = await get_cross_references(test_db, uuid.UUID(sample_verse.id))
    assert refs == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_cross_references_with_data(test_db, sample_verse, sample_nt_book, sample_translation):
    """Test getting cross-references when they exist."""
    from tests.conftest import Verse, CrossReference
    from search import get_cross_references

    # Create a related verse - commit it first before referencing in cross_ref
    related_verse = Verse(
        id=str(uuid.uuid4()),
        translation_id=sample_translation.id,
        book_id=sample_nt_book.id,
        chapter=5,
        verse=44,
        text="But I say to you, Love your enemies.",
    )
    test_db.add(related_verse)
    await test_db.flush()  # Ensure verse exists before creating cross-reference
    # flush works in async session too if autocommit is false

    # Create cross-reference
    cross_ref = CrossReference(
        id=str(uuid.uuid4()),
        verse_id=sample_verse.id,
        related_verse_id=related_verse.id,
        relationship_type="parallel",
        confidence=0.95,
    )
    test_db.add(cross_ref)
    await test_db.commit()
    await test_db.refresh(related_verse)

    refs = await get_cross_references(test_db, uuid.UUID(sample_verse.id), limit=10)
    assert len(refs) == 1
    assert refs[0]["relationship"] == "parallel"
    assert refs[0]["book"] == "Matthew"
    assert refs[0]["chapter"] == 5
    assert refs[0]["verse"] == 44
    assert refs[0]["confidence"] == 0.95


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_original_words_none(test_db, sample_verse):
    """Test getting original words when none exist."""
    from search import get_original_words

    result = await get_original_words(test_db, uuid.UUID(sample_verse.id))
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_original_words_with_data(test_db, sample_verse):
    """Test getting original words when they exist."""
    from tests.conftest import OriginalWord
    from search import get_original_words

    # Add some Greek words
    words_data = [
        {
            "word": "ἐν",
            "transliteration": "en",
            "strongs": "G1722",
            "definition": "in, on, among",
            "word_order": 1,
        },
        {
            "word": "ἀρχῇ",
            "transliteration": "archē",
            "strongs": "G746",
            "definition": "beginning, origin",
            "word_order": 2,
        },
    ]

    for word_data in words_data:
        word = OriginalWord(
            id=str(uuid.uuid4()),
            verse_id=sample_verse.id,
            word=word_data["word"],
            language="greek",
            strongs_number=word_data["strongs"],
            transliteration=word_data["transliteration"],
            definition=word_data["definition"],
            morphology=None,
            word_order=word_data["word_order"],
        )
        test_db.add(word)
    await test_db.commit()

    result = await get_original_words(test_db, uuid.UUID(sample_verse.id))
    assert result is not None
    assert result["language"] == "greek"
    assert len(result["words"]) == 2
    assert result["words"][0]["strongs"] == "G1722"
    assert result["words"][1]["word"] == "ἀρχῇ"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_verse_by_reference_book_not_found(test_db):
    """Test getting verse with invalid book name."""
    from search import get_verse_by_reference

    result = await get_verse_by_reference(
        db=test_db,
        book="NonexistentBook",
        chapter=1,
        verse=1,
    )
    assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_verse_by_reference_success(test_db, sample_book, sample_translation, sample_verse):
    """Test getting verse by reference successfully."""
    from search import get_verse_by_reference

    # Ensure data is committed before searching
    await test_db.commit()

    result = await get_verse_by_reference(
        db=test_db,
        book="Genesis",
        chapter=1,
        verse=1,
        translations=["TEV"],
        include_original=False,
        include_cross_refs=False,  # Don't include cross-refs to avoid extra queries
    )

    assert result is not None
    assert result["reference"]["book"] == "Genesis"
    assert result["reference"]["chapter"] == 1
    assert result["reference"]["verse"] == 1
    assert "TEV" in result["translations"]
    assert "In the beginning" in result["translations"]["TEV"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_verse_by_reference_korean_name(test_db, sample_book, sample_translation, sample_verse):
    """Test getting verse using Korean book name."""
    from search import get_verse_by_reference

    # Ensure data is committed
    await test_db.commit()

    result = await get_verse_by_reference(
        db=test_db,
        book="창세기",
        chapter=1,
        verse=1,
        include_original=False,
        include_cross_refs=False,
    )

    assert result is not None
    assert result["reference"]["book"] == "Genesis"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_verse_by_reference_abbreviation(test_db, sample_book, sample_translation, sample_verse):
    """Test getting verse using book abbreviation."""
    from search import get_verse_by_reference

    # Ensure data is committed
    await test_db.commit()

    result = await get_verse_by_reference(
        db=test_db,
        book="Gen",
        chapter=1,
        verse=1,
        include_original=False,
        include_cross_refs=False,
    )

    assert result is not None
    assert result["reference"]["book"] == "Genesis"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_verse_context(test_db, sample_book, sample_translation):
    """Test getting verse context (previous/next verses)."""
    from tests.conftest import Verse
    from search import get_verse_context

    # Create multiple verses
    verses = []
    for i in range(1, 4):
        verse = Verse(
            id=str(uuid.uuid4()),
            translation_id=sample_translation.id,
            book_id=sample_book.id,
            chapter=1,
            verse=i,
            text=f"This is verse {i}.",
        )
        test_db.add(verse)
        verses.append(verse)
    await test_db.commit()

    # Refresh verses to ensure they're properly loaded
    for v in verses:
        await test_db.refresh(v)

    # Get context for verse 2 - convert book_id string to UUID
    context = await get_verse_context(test_db, uuid.UUID(sample_book.id), 1, 2)

    assert context["previous"] is not None
    assert context["previous"]["verse"] == 1
    assert "This is verse 1" in context["previous"]["text"]

    assert context["next"] is not None
    assert context["next"]["verse"] == 3
    assert "This is verse 3" in context["next"]["text"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_search_by_theme(test_db, sample_translation):
    """Test thematic search."""
    from search import search_by_theme

    # We need to mock await search_verses (which is an async function)
    # Patching async functions requires returning a coroutine or AsyncMock
    # Or we can patch search_verses directly.
    # Since search_by_theme calls await search_verses, the mock must be awaitable.
    
    with patch("search.search_verses") as mock_search:
        # Configure mock to be awaitable
        async def mock_async_search(**kwargs):
            return {
                "query_time_ms": 100,
                "results": [],
                "search_metadata": {"total_results": 0},
            }
        
        mock_search.side_effect = mock_async_search

        results = await search_by_theme(
            db=test_db,
            theme="love",
            translations=["TEV"],
            testament="NT",
            max_results=20,
        )

        assert "theme" in results
        assert results["theme"] == "love"
        assert "testament_filter" in results
        assert results["testament_filter"] == "NT"

        # Verify search_verses was called
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["filters"]["testament"] == "NT"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_search_by_theme_both_testaments(test_db, sample_translation):
    """Test thematic search with 'both' testament filter."""
    from search import search_by_theme

    with patch("search.search_verses") as mock_search:
        async def mock_async_search(**kwargs):
            return {
                "query_time_ms": 100,
                "results": [],
                "search_metadata": {"total_results": 0},
            }
        mock_search.side_effect = mock_async_search

        results = await search_by_theme(
            db=test_db,
            theme="faith",
            translations=["TEV"],
            testament="both",
            max_results=20,
        )

        # 'both' should result in no testament filter
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["filters"] == {}
