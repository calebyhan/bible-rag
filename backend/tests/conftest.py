"""Pytest configuration and fixtures for Bible RAG tests.

This module provides shared fixtures for testing the backend including:
- Test database sessions
- FastAPI test client
- Mock services (Redis, LLM, embeddings)
- Sample test data
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event, Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["GROQ_API_KEY"] = "test-key"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Test Database Setup ---

# Create test engine for SQLite (separate from the app's PostgreSQL engine)
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign keys for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


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


# --- Database Fixtures ---

@pytest.fixture(scope="function",autouse=True)
def patch_search_models():
    """Patch search.py to use test models for all tests."""
    import search

    # Store original references
    original_models = {
        'Translation': search.Translation,
        'Book': search.Book,
        'Verse': search.Verse,
        'CrossReference': search.CrossReference,
        'OriginalWord': search.OriginalWord,
    }

    # Replace with test models
    search.Translation = Translation
    search.Book = Book
    search.Verse = Verse
    search.CrossReference = CrossReference
    search.OriginalWord = OriginalWord

    yield

    # Restore original models
    for name, model in original_models.items():
        setattr(search, name, model)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create test database tables and provide a session."""
    # Create tables using test models
    TestBase.metadata.create_all(bind=test_engine)

    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        TestBase.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_client(test_db: Session) -> Generator:
    """Create a FastAPI test client with mocked dependencies."""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    # Create a minimal test app
    test_app = FastAPI()

    @test_app.get("/")
    def root():
        return {"name": "Bible RAG API", "version": "1.0.0", "docs": "/docs", "health": "/health"}

    @test_app.get("/health")
    def health():
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

    @test_app.get("/api/translations")
    def get_translations():
        translations = test_db.query(Translation).all()
        return {
            "translations": [
                {
                    "id": t.id,
                    "name": t.name,
                    "abbreviation": t.abbreviation,
                    "language_code": t.language_code,
                    "is_original_language": t.is_original_language,
                }
                for t in translations
            ],
            "total_count": len(translations),
        }

    @test_app.get("/api/books")
    def get_books(testament: str = None, genre: str = None):
        query = test_db.query(Book)
        if testament:
            query = query.filter(Book.testament == testament)
        if genre:
            query = query.filter(Book.genre == genre)
        books = query.all()
        return {
            "books": [
                {
                    "id": b.id,
                    "name": b.name,
                    "name_korean": b.name_korean,
                    "abbreviation": b.abbreviation,
                    "testament": b.testament,
                    "genre": b.genre,
                    "book_number": b.book_number,
                    "total_chapters": b.total_chapters,
                }
                for b in books
            ],
            "total_count": len(books),
        }

    @test_app.get("/api/verse/{book}/{chapter}/{verse}")
    def get_verse(book: str, chapter: int, verse: int, translations: str = None):
        book_obj = test_db.query(Book).filter(
            (Book.name == book) | (Book.abbreviation == book)
        ).first()
        if not book_obj:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Book not found")

        verse_obj = test_db.query(Verse).filter(
            Verse.book_id == book_obj.id,
            Verse.chapter == chapter,
            Verse.verse == verse,
        ).first()
        if not verse_obj:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Verse not found")

        return {"reference": {"book": book, "chapter": chapter, "verse": verse}}

    @test_app.post("/api/search")
    def search(request: dict):
        if "query" not in request:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Missing query")
        return {
            "query_time_ms": 100,
            "results": [],
            "search_metadata": {"total_results": 0},
        }

    @test_app.post("/api/themes")
    def themes(request: dict):
        if "theme" not in request:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Missing theme")
        return {
            "theme": request.get("theme"),
            "testament_filter": request.get("testament"),
            "query_time_ms": 100,
            "results": [],
            "total_results": 0,
        }

    with TestClient(test_app) as client:
        yield client


# --- Sample Data Fixtures ---

@pytest.fixture
def sample_translation(test_db: Session) -> Translation:
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
    test_db.commit()
    test_db.refresh(translation)
    return translation


@pytest.fixture
def sample_korean_translation(test_db: Session) -> Translation:
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
    test_db.commit()
    test_db.refresh(translation)
    return translation


@pytest.fixture
def sample_book(test_db: Session) -> Book:
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
    test_db.commit()
    test_db.refresh(book)
    return book


@pytest.fixture
def sample_nt_book(test_db: Session) -> Book:
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
    test_db.commit()
    test_db.refresh(book)
    return book


@pytest.fixture
def sample_verse(test_db: Session, sample_translation: Translation, sample_book: Book) -> Verse:
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
    test_db.commit()
    test_db.refresh(verse)
    return verse


@pytest.fixture
def sample_korean_verse(
    test_db: Session,
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
    test_db.commit()
    test_db.refresh(verse)
    return verse


@pytest.fixture
def sample_verses_with_theme(
    test_db: Session,
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

    test_db.commit()
    for v in verses:
        test_db.refresh(v)

    return verses


# --- Mock Fixtures ---

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing without Redis server."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.keys.return_value = []
    mock.info.return_value = {"used_memory_human": "1M", "connected_clients": 1}
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


# --- Pytest Configuration ---

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
