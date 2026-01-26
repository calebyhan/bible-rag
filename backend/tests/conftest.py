"""Pytest configuration and fixtures for Bible RAG tests.

This module provides shared fixtures for testing the backend including:
- Test database sessions (Async)
- FastAPI test client (Async)
- Mock services (Redis, LLM, embeddings)
- Sample test data
"""

import os
import sys
import uuid
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import event, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import String, Text, Boolean, DateTime, Integer, Float
from sqlalchemy.schema import ForeignKey

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["GROQ_API_KEY"] = "test-key"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db

# --- Test Database Setup ---

# Create test engine for SQLite (separate from the app's PostgreSQL engine)
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(test_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# --- Test Models (SQLite-compatible) ---

class TestBase(DeclarativeBase):
    """Base class for test models."""
    pass


class Translation(TestBase):
    """Bible translation metadata - test version."""
    __tablename__ = "translations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    abbreviation: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    language_code: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_original_language: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Book(TestBase):
    """Bible book metadata - test version."""
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_korean: Mapped[str] = mapped_column(Text, nullable=True)
    name_original: Mapped[str] = mapped_column(Text, nullable=True)
    abbreviation: Mapped[str] = mapped_column(Text, nullable=False)
    testament: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[str] = mapped_column(Text, nullable=True)
    book_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    total_chapters: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Verse(TestBase):
    """Bible verse - test version."""
    __tablename__ = "verses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    translation_id: Mapped[str] = mapped_column(String(36), ForeignKey("translations.id"), nullable=False)
    book_id: Mapped[str] = mapped_column(String(36), ForeignKey("books.id"), nullable=False)
    chapter: Mapped[int] = mapped_column(Integer, nullable=False)
    verse: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrossReference(TestBase):
    """Cross-reference between verses - test version."""
    __tablename__ = "cross_references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    verse_id: Mapped[str] = mapped_column(String(36), ForeignKey("verses.id"), nullable=False)
    related_verse_id: Mapped[str] = mapped_column(String(36), ForeignKey("verses.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OriginalWord(TestBase):
    """Original language word - test version."""
    __tablename__ = "original_words"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    verse_id: Mapped[str] = mapped_column(String(36), ForeignKey("verses.id"), nullable=False)
    word: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False)
    strongs_number: Mapped[str] = mapped_column(Text, nullable=True)
    transliteration: Mapped[str] = mapped_column(Text, nullable=True)
    morphology: Mapped[str] = mapped_column(Text, nullable=True)
    definition: Mapped[str] = mapped_column(Text, nullable=True)
    word_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Embedding(TestBase):
    """Embedding model - test version (SQLite compatible)."""
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    verse_id: Mapped[str] = mapped_column(String(36), ForeignKey("verses.id"), nullable=False)
    vector: Mapped[str] = mapped_column(Text, nullable=True) 
    model_version: Mapped[str] = mapped_column(Text, default="test-model")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# --- Database Fixtures ---

@pytest_asyncio.fixture(scope="function", autouse=True)
async def patch_search_models():
    """Patch search.py to use test models for all tests."""
    import search

    # Store original references
    original_models = {
        'Translation': search.Translation,
        'Book': search.Book,
        'Verse': search.Verse,
        'CrossReference': search.CrossReference,
        'OriginalWord': search.OriginalWord,
        'Embedding': search.Embedding,
    }

    # Replace with test models
    search.Translation = Translation
    search.Book = Book
    search.Verse = Verse
    search.CrossReference = CrossReference
    search.OriginalWord = OriginalWord
    search.Embedding = Embedding

    yield

    # Restore original models
    for name, model in original_models.items():
        setattr(search, name, model)


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database tables and provide a session."""
    # Create tables using test models
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_client(test_db: AsyncSession, mock_redis) -> AsyncGenerator:
    """Create a FastAPI test client with mocked dependencies."""
    from httpx import AsyncClient, ASGITransport
    from fastapi import FastAPI
    from cache import get_cache
    
    # Import routers - we need to ensure imports work and rely on same db dependency
    from routers import metadata, search, verses, themes, health

    test_app = FastAPI()
    
    # Mount routers
    test_app.include_router(metadata.router)
    test_app.include_router(search.router) # /api/search
    test_app.include_router(verses.router) # /api/verse /api/chapter
    test_app.include_router(themes.router) # /api/themes
    test_app.include_router(health.router) # /health
    
    # Patch get_cache in checking locations
    patch_health_cache = patch("routers.health.get_cache", return_value=mock_redis)
    patch_health_cache.start()
    
    patch_search_cache = patch("search.get_cache", return_value=mock_redis)
    patch_search_cache.start()
    
    patch_embed = patch("search.embed_query", side_effect=lambda q, **k: [0.1] * 1024)
    patch_embed.start()
    
    # Patch fulltext search to avoid Postgres specific SQL on SQLite
    async def mock_fulltext(*args, **kwargs):
        # Return valid search response structure
        return {
            "query_time_ms": 0,
            "results": [],
            "search_metadata": {
                "total_results": 0,
                "embedding_model": None,
                "search_method": "full-text",
                "cached": False,
            }
        }
    patch_fulltext = patch("search.fulltext_search_verses", side_effect=mock_fulltext)
    patch_fulltext.start()

    # Add root route as defined in tests
    @test_app.get("/")
    async def root():
        return {"name": "Bible RAG API", "version": "1.0.0", "docs": "/docs", "health": "/health"}

    # Override dependencies
    async def override_get_db():
        yield test_db
        
    def override_get_cache():
        return mock_redis

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_cache] = override_get_cache

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


# --- Sample Data Fixtures ---

@pytest_asyncio.fixture
async def sample_translation(test_db: AsyncSession) -> Translation:
    """Create a sample translation for testing."""
    translation = Translation(
        id=str(uuid.uuid4()),
        name="Test English Version",
        abbreviation="TEV",
        language_code="en",
        description="A test translation",
        is_original_language=False,
    )
    test_db.add(translation)
    await test_db.commit()
    await test_db.refresh(translation)
    return translation


@pytest_asyncio.fixture
async def sample_korean_translation(test_db: AsyncSession) -> Translation:
    """Create a sample Korean translation for testing."""
    translation = Translation(
        id=str(uuid.uuid4()),
        name="테스트 한국어 성경",
        abbreviation="TKV",
        language_code="ko",
        description="테스트용 한국어 번역",
        is_original_language=False,
    )
    test_db.add(translation)
    await test_db.commit()
    await test_db.refresh(translation)
    return translation


@pytest_asyncio.fixture
async def sample_book(test_db: AsyncSession) -> Book:
    """Create a sample book for testing."""
    book = Book(
        id=str(uuid.uuid4()),
        name="Genesis",
        name_korean="창세기",
        abbreviation="Gen",
        testament="OT",
        genre="law",
        book_number=1,
        total_chapters=50,
    )
    test_db.add(book)
    await test_db.commit()
    await test_db.refresh(book)
    return book


@pytest_asyncio.fixture
async def sample_nt_book(test_db: AsyncSession) -> Book:
    """Create a sample New Testament book for testing."""
    book = Book(
        id=str(uuid.uuid4()),
        name="Matthew",
        name_korean="마태복음",
        abbreviation="Matt",
        testament="NT",
        genre="gospel",
        book_number=40,
        total_chapters=28,
    )
    test_db.add(book)
    await test_db.commit()
    await test_db.refresh(book)
    return book


@pytest_asyncio.fixture
async def sample_verse(test_db: AsyncSession, sample_translation: Translation, sample_book: Book) -> Verse:
    """Create a sample verse for testing."""
    verse = Verse(
        id=str(uuid.uuid4()),
        translation_id=sample_translation.id,
        book_id=sample_book.id,
        chapter=1,
        verse=1,
        text="In the beginning God created the heavens and the earth.",
    )
    test_db.add(verse)
    await test_db.commit()
    await test_db.refresh(verse)
    return verse


@pytest_asyncio.fixture
async def sample_korean_verse(
    test_db: AsyncSession,
    sample_korean_translation: Translation,
    sample_book: Book
) -> Verse:
    """Create a sample Korean verse for testing."""
    verse = Verse(
        id=str(uuid.uuid4()),
        translation_id=sample_korean_translation.id,
        book_id=sample_book.id,
        chapter=1,
        verse=1,
        text="태초에 하나님이 천지를 창조하시니라",
    )
    test_db.add(verse)
    await test_db.commit()
    await test_db.refresh(verse)
    return verse


@pytest_asyncio.fixture
async def sample_verses_with_theme(
    test_db: AsyncSession,
    sample_translation: Translation,
    sample_nt_book: Book,
) -> list[Verse]:
    """Create sample verses about love for thematic testing."""
    verses_data = [
        (5, 44, "But I say to you, Love your enemies and pray for those who persecute you."),
        (22, 37, "You shall love the Lord your God with all your heart and soul and mind."),
        (22, 39, "And a second is like it: You shall love your neighbor as yourself."),
    ]

    verses = []
    for chapter, verse_num, text in verses_data:
        verse = Verse(
            id=str(uuid.uuid4()),
            translation_id=sample_translation.id,
            book_id=sample_nt_book.id,
            chapter=chapter,
            verse=verse_num,
            text=text,
        )
        test_db.add(verse)
        verses.append(verse)

    await test_db.commit() 
    
    cleaned_verses = []
    for v in verses:
        await test_db.refresh(v)
        cleaned_verses.append(v)

    return cleaned_verses


@pytest_asyncio.fixture
async def sample_verse_with_original(test_db: AsyncSession, sample_verse: Verse) -> Verse:
    """Create a sample verse with original words."""
    # Create original words linked to the sample verse
    word1 = OriginalWord(
        id=str(uuid.uuid4()),
        verse_id=sample_verse.id,
        word="In beginning",
        language="hebrew",
        strongs_number="H7225",
        transliteration="bereshith",
        morphology="Noun",
        definition="in the beginning",
        word_order=1,
    )
    word2 = OriginalWord(
        id=str(uuid.uuid4()),
        verse_id=sample_verse.id,
        word="created",
        language="hebrew",
        strongs_number="H1254",
        transliteration="bara",
        morphology="Verb",
        definition="create",
        word_order=2,
    )
    test_db.add(word1)
    test_db.add(word2)
    await test_db.commit()
    await test_db.refresh(sample_verse)
    return sample_verse


@pytest.fixture
def mock_redis():
    """Mock Redis client/wrapper for testing."""
    mock = MagicMock()
    # Mock RedisCache methods
    mock.is_connected.return_value = True
    mock.get_cache_stats.return_value = {"cached_searches": 0}
    mock.get_cached_verse.return_value = None
    mock.get_cached_results.return_value = None
    
    # Mock client methods (if accessed directly)
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.keys.return_value = []
    mock.info.return_value = {"used_memory_human": "1M", "connected_clients": 1}
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model to avoid loading actual model in tests."""
    mock = MagicMock()
    # Return a fake 1024-dimensional embedding
    mock.encode.return_value = [[0.1] * 1024]
    return mock


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing without API calls."""
    return "This is a test AI response about the biblical passage."


@pytest.fixture
def mock_gemini(mock_llm_response):
    """Mock Google Gemini API."""
    with patch("llm.genai") as mock_genai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = mock_llm_response
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        yield mock_genai


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring real services"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
