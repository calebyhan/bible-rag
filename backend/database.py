"""Database models and connection management for Bible RAG."""

import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool
import os

from config import get_settings

settings = get_settings()

# Database engine with connection pooling
# Use SQLite for testing to avoid PostgreSQL dependency
if os.getenv("DATABASE_URL", "").startswith("sqlite"):
    # SQLite doesn't support pool_size/max_overflow parameters
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug,
    )
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        settings.database_url,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Translation(Base):
    """Bible translation metadata."""

    __tablename__ = "translations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    abbreviation: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    language_code: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_original_language: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    verses: Mapped[list["Verse"]] = relationship(
        "Verse", back_populates="translation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_translations_language", "language_code"),
        Index("idx_translations_abbrev", "abbreviation"),
    )


class Book(Base):
    """Bible book metadata."""

    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_korean: Mapped[Optional[str]] = mapped_column(Text)
    name_original: Mapped[Optional[str]] = mapped_column(Text)
    abbreviation: Mapped[str] = mapped_column(Text, nullable=False)
    testament: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[Optional[str]] = mapped_column(Text)
    book_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    total_chapters: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    verses: Mapped[list["Verse"]] = relationship(
        "Verse", back_populates="book", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("testament IN ('OT', 'NT')", name="check_testament"),
        Index("idx_books_testament", "testament"),
        Index("idx_books_genre", "genre"),
        Index("idx_books_number", "book_number"),
    )


class Verse(Base):
    """Bible verse text for each translation."""

    __tablename__ = "verses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    translation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("translations.id", ondelete="CASCADE"), nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    chapter: Mapped[int] = mapped_column(Integer, nullable=False)
    verse: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    translation: Mapped["Translation"] = relationship("Translation", back_populates="verses")
    book: Mapped["Book"] = relationship("Book", back_populates="verses")
    embedding: Mapped[Optional["Embedding"]] = relationship(
        "Embedding", back_populates="verse", uselist=False, cascade="all, delete-orphan"
    )
    original_words: Mapped[list["OriginalWord"]] = relationship(
        "OriginalWord", back_populates="verse", cascade="all, delete-orphan"
    )
    cross_references_from: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        foreign_keys="CrossReference.verse_id",
        back_populates="verse",
        cascade="all, delete-orphan",
    )
    cross_references_to: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        foreign_keys="CrossReference.related_verse_id",
        back_populates="related_verse",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("translation_id", "book_id", "chapter", "verse", name="uq_verse"),
        CheckConstraint("chapter >= 1", name="check_chapter"),
        CheckConstraint("verse >= 1", name="check_verse"),
        Index("idx_verses_translation", "translation_id"),
        Index("idx_verses_book", "book_id"),
        Index("idx_verses_book_chapter", "book_id", "chapter"),
    )


class Embedding(Base):
    """Vector embeddings for semantic search."""

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    verse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verses.id", ondelete="CASCADE"), nullable=False
    )
    vector = mapped_column(Vector(1024), nullable=False)
    model_version: Mapped[str] = mapped_column(
        Text, nullable=False, default="multilingual-e5-large"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    verse: Mapped["Verse"] = relationship("Verse", back_populates="embedding")

    __table_args__ = (
        UniqueConstraint("verse_id", "model_version", name="uq_embedding_verse_model"),
        Index("idx_embeddings_verse", "verse_id"),
    )


class CrossReference(Base):
    """Cross-references between verses."""

    __tablename__ = "cross_references"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    verse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verses.id", ondelete="CASCADE"), nullable=False
    )
    related_verse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verses.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    verse: Mapped["Verse"] = relationship(
        "Verse", foreign_keys=[verse_id], back_populates="cross_references_from"
    )
    related_verse: Mapped["Verse"] = relationship(
        "Verse", foreign_keys=[related_verse_id], back_populates="cross_references_to"
    )

    __table_args__ = (
        UniqueConstraint(
            "verse_id", "related_verse_id", "relationship_type", name="uq_cross_reference"
        ),
        CheckConstraint(
            "relationship_type IN ('parallel', 'prophecy-fulfillment', 'quotation', 'allusion', 'thematic')",
            name="check_relationship_type",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="check_confidence",
        ),
        Index("idx_cross_refs_verse", "verse_id"),
        Index("idx_cross_refs_related", "related_verse_id"),
        Index("idx_cross_refs_type", "relationship_type"),
    )


class OriginalWord(Base):
    """Original language word data (Greek, Hebrew, Aramaic)."""

    __tablename__ = "original_words"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    verse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verses.id", ondelete="CASCADE"), nullable=False
    )
    word: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False)
    strongs_number: Mapped[Optional[str]] = mapped_column(Text)
    transliteration: Mapped[Optional[str]] = mapped_column(Text)
    morphology: Mapped[Optional[str]] = mapped_column(Text)
    definition: Mapped[Optional[str]] = mapped_column(Text)
    word_order: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    verse: Mapped["Verse"] = relationship("Verse", back_populates="original_words")

    __table_args__ = (
        CheckConstraint(
            "language IN ('greek', 'hebrew', 'aramaic')", name="check_language"
        ),
        Index("idx_original_words_verse", "verse_id"),
        Index("idx_original_words_strongs", "strongs_number"),
        Index("idx_original_words_language", "language"),
    )


class QueryCache(Base):
    """Cache for search query results."""

    __tablename__ = "query_cache"

    query_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[Optional[str]] = mapped_column(Text)
    translations: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text))
    results: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    hit_count: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    __table_args__ = (
        Index("idx_query_cache_expires", "expires_at"),
        Index("idx_query_cache_hit_count", "hit_count"),
        Index("idx_query_cache_language", "language_code"),
    )


def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database schema."""
    Base.metadata.create_all(bind=engine)
    print("Database schema created successfully!")


def create_vector_index(db_session=None):
    """Create ivfflat index for vector similarity search.

    Should be called after all embeddings are inserted.
    """
    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True

    try:
        # Drop existing index if it exists
        db_session.execute(text("DROP INDEX IF EXISTS idx_embeddings_vector"))

        # Create ivfflat index
        db_session.execute(
            text(
                """
                CREATE INDEX idx_embeddings_vector
                ON embeddings
                USING ivfflat (vector vector_cosine_ops)
                WITH (lists = 100)
                """
            )
        )
        db_session.commit()
        print("Vector index created successfully!")
    except Exception as e:
        db_session.rollback()
        raise e
    finally:
        if close_session:
            db_session.close()


if __name__ == "__main__":
    init_db()
