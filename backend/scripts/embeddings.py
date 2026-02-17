"""Embedding generation for Bible verses.

This module handles loading the multilingual embedding model and generating
vector embeddings for all verses in the database.
"""

import argparse
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional
from uuid import UUID

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from tqdm import tqdm

from config import get_settings
from database import Book, Embedding, SessionLocal, Verse

settings = get_settings()


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the embedding model.

    Uses multilingual-e5-large for best Korean language support.
    """
    print(f"Loading embedding model: {settings.embedding_model}")
    model = SentenceTransformer(settings.embedding_model)
    print("Model loaded successfully!")
    return model


def embed_texts(texts: list[str], normalize: bool = True) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed
        normalize: Whether to L2 normalize embeddings (recommended for cosine similarity)

    Returns:
        numpy array of shape (len(texts), embedding_dimension)
    """
    model = get_embedding_model()

    # For e5 models, prepend "query: " or "passage: " prefix
    # Using "passage: " for stored verses, "query: " for search queries
    prefixed_texts = [f"passage: {text}" for text in texts]

    embeddings = model.encode(
        prefixed_texts,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )

    return embeddings


def embed_query(query: str, normalize: bool = True) -> np.ndarray:
    """Generate embedding for a search query.

    Args:
        query: Search query string
        normalize: Whether to L2 normalize

    Returns:
        numpy array of shape (embedding_dimension,)
    """
    model = get_embedding_model()

    # For e5 models, use "query: " prefix for search queries
    prefixed_query = f"query: {query}"

    embedding = model.encode(
        prefixed_query,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )

    return embedding


def get_verses_without_embeddings(
    db: Session,
    translation_id: Optional[UUID] = None,
    limit: Optional[int] = None,
) -> list[Verse]:
    """Get verses that don't have embeddings yet.

    Args:
        db: Database session
        translation_id: Optional filter by translation
        limit: Optional limit on number of verses

    Returns:
        List of Verse objects
    """
    query = db.query(Verse).options(joinedload(Verse.book)).outerjoin(Embedding).filter(Embedding.id.is_(None))

    if translation_id:
        query = query.filter(Verse.translation_id == translation_id)

    query = query.order_by(Verse.id)

    if limit:
        query = query.limit(limit)

    return query.all()


def _build_contextual_text(verse: Verse) -> str:
    """Build contextual embedding text with book/chapter/testament metadata."""
    book = verse.book
    if book:
        return f"[{book.name} {verse.chapter}:{verse.verse}, {book.testament}, {book.genre}] {verse.text}"
    return verse.text


def embed_verses_batch(
    db: Session,
    verses: list[Verse],
    batch_size: int = 32,
    model_version: str = "multilingual-e5-large-ctx",
) -> int:
    """Generate embeddings for a batch of verses.

    Embeds verses with contextual metadata (book name, chapter:verse,
    testament, genre) prepended to improve semantic understanding.

    Args:
        db: Database session
        verses: List of Verse objects to embed (must have book relationship loaded)
        batch_size: Number of verses to embed at once
        model_version: Model version string for tracking

    Returns:
        Number of embeddings created
    """
    count = 0
    total_batches = (len(verses) + batch_size - 1) // batch_size

    for i in tqdm(range(0, len(verses), batch_size), total=total_batches, desc="Embedding"):
        batch_verses = verses[i : i + batch_size]
        texts = [_build_contextual_text(verse) for verse in batch_verses]

        # Generate embeddings
        embeddings = embed_texts(texts)

        # Create Embedding records
        for verse, embedding in zip(batch_verses, embeddings):
            # Check if embedding already exists
            existing = (
                db.query(Embedding)
                .filter(
                    Embedding.verse_id == verse.id,
                    Embedding.model_version == model_version,
                )
                .first()
            )

            if existing:
                continue

            emb = Embedding(
                verse_id=verse.id,
                vector=embedding.tolist(),
                model_version=model_version,
            )
            db.add(emb)
            count += 1

        db.commit()

    return count


def embed_all_verses(
    translation_id: Optional[UUID] = None,
    batch_size: int = 32,
    force: bool = False,
    build_index: bool = True,
):
    """Generate embeddings for all verses in the database.

    Args:
        translation_id: Optional filter by translation
        batch_size: Number of verses to embed at once
        force: If True, regenerate all embeddings even if they exist
        build_index: If True, build the vector index after embedding
    """
    db = SessionLocal()

    try:
        # Get verses to embed
        if force:
            query = db.query(Verse).options(joinedload(Verse.book))
            if translation_id:
                query = query.filter(Verse.translation_id == translation_id)
            verses = query.all()

            # Delete existing embeddings if forcing regeneration
            if verses:
                verse_ids = [v.id for v in verses]
                db.query(Embedding).filter(Embedding.verse_id.in_(verse_ids)).delete(
                    synchronize_session=False
                )
                db.commit()
        else:
            verses = get_verses_without_embeddings(db, translation_id)

        if not verses:
            print("No verses to embed")
            return

        print(f"Found {len(verses)} verses to embed")

        # Preload the model
        print("Loading embedding model...")
        get_embedding_model()

        # Generate embeddings
        count = embed_verses_batch(db, verses, batch_size)
        print(f"Created {count} embeddings")

        # Build vector index
        if build_index:
            print("Building vector index...")
            db.execute(text("DROP INDEX IF EXISTS idx_embeddings_vector"))
            db.execute(
                text(
                    "CREATE INDEX idx_embeddings_vector "
                    "ON embeddings USING hnsw (vector vector_cosine_ops)"
                )
            )
            db.commit()
            print("Vector index created successfully!")

        # Verify
        total_embeddings = db.query(Embedding).count()
        print(f"Total embeddings in database: {total_embeddings}")

    finally:
        db.close()


def verify_embeddings(db: Session) -> dict:
    """Verify embedding status.

    Returns:
        Dictionary with verification statistics
    """
    total_verses = db.query(Verse).count()
    total_embeddings = db.query(Embedding).count()
    verses_without_embeddings = len(get_verses_without_embeddings(db))

    # Check embedding dimensions
    sample = db.query(Embedding).first()
    dimension = len(sample.vector) if sample else 0

    # Check index status
    index_exists = False
    try:
        result = db.execute(
            text(
                "SELECT indexname FROM pg_indexes WHERE indexname = 'idx_embeddings_vector'"
            )
        )
        index_exists = result.fetchone() is not None
    except Exception:
        pass

    return {
        "total_verses": total_verses,
        "total_embeddings": total_embeddings,
        "verses_without_embeddings": verses_without_embeddings,
        "embedding_dimension": dimension,
        "vector_index_exists": index_exists,
        "coverage_percent": (
            round(total_embeddings / total_verses * 100, 2) if total_verses > 0 else 0
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for Bible verses")
    parser.add_argument(
        "--translation",
        type=str,
        help="Translation ID to embed (optional, embeds all if not specified)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding (default: 32)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration of all embeddings",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip building the vector index",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify existing embeddings, don't generate new ones",
    )

    args = parser.parse_args()

    if args.verify:
        db = SessionLocal()
        try:
            stats = verify_embeddings(db)
            print("\nEmbedding Status:")
            print(f"  Total verses: {stats['total_verses']}")
            print(f"  Total embeddings: {stats['total_embeddings']}")
            print(f"  Missing embeddings: {stats['verses_without_embeddings']}")
            print(f"  Embedding dimension: {stats['embedding_dimension']}")
            print(f"  Vector index exists: {stats['vector_index_exists']}")
            print(f"  Coverage: {stats['coverage_percent']}%")
        finally:
            db.close()
    else:
        translation_id = UUID(args.translation) if args.translation else None
        embed_all_verses(
            translation_id=translation_id,
            batch_size=args.batch_size,
            force=args.force,
            build_index=not args.no_index,
        )
