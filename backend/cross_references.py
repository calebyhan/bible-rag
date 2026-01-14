"""Cross-reference generation and management for Bible verses.

This module handles:
1. Fetching cross-reference data from OpenBible.info
2. Generating cross-references based on semantic similarity
3. Populating the cross_references table
"""

import json
import logging
from typing import Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from database import Book, CrossReference, SessionLocal, Verse

logger = logging.getLogger(__name__)


class CrossReferenceManager:
    """Manages cross-reference data for Bible verses."""

    # OpenBible.info cross-reference data
    OPENBIBLE_URL = "https://raw.githubusercontent.com/openbibleinfo/Bible-Cross-Reference-JSON/master/cross_references.json"

    # Relationship type mapping from OpenBible data
    RELATIONSHIP_TYPES = {
        "quotation": "quotation",  # OT quoted in NT
        "allusion": "allusion",  # Indirect reference
        "parallel": "parallel",  # Similar passages (e.g., Gospel parallels)
        "theme": "thematic",  # Thematic connection
    }

    def __init__(self, db: Optional[Session] = None):
        """Initialize the cross-reference manager.

        Args:
            db: Database session. If None, creates new session.
        """
        self.db = db or SessionLocal()
        self._should_close_db = db is None

    def __del__(self):
        """Close database session if we created it."""
        if self._should_close_db and self.db:
            self.db.close()

    async def fetch_openbible_data(self) -> List[Dict]:
        """Fetch cross-reference data from OpenBible.info.

        Returns:
            List of cross-reference dictionaries.

        Raises:
            httpx.HTTPError: If fetching data fails.
        """
        logger.info(f"Fetching cross-reference data from {self.OPENBIBLE_URL}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(self.OPENBIBLE_URL)
            response.raise_for_status()
            data = response.json()

        logger.info(f"Fetched {len(data)} cross-references from OpenBible.info")
        return data

    def parse_verse_reference(self, ref: str) -> Optional[tuple[str, int, int]]:
        """Parse a verse reference string into components.

        Supports formats like:
        - Gen.1.1
        - Genesis 1:1
        - Matt.5.3
        - Matthew 5:3

        Args:
            ref: Verse reference string.

        Returns:
            Tuple of (book_abbrev, chapter, verse) or None if parsing fails.
        """
        try:
            # Handle formats like "Gen.1.1"
            if "." in ref:
                parts = ref.split(".")
                if len(parts) == 3:
                    book_abbrev, chapter, verse = parts
                    return (book_abbrev, int(chapter), int(verse))

            # Handle formats like "Genesis 1:1"
            if ":" in ref:
                book_part, verse_part = ref.rsplit(":", 1)
                if " " in book_part:
                    book, chapter = book_part.rsplit(" ", 1)
                    return (book.strip(), int(chapter), int(verse_part))

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse verse reference '{ref}': {e}")

        return None

    def find_verse_by_reference(
        self, book_name: str, chapter: int, verse: int, translation_abbrev: str = "NIV"
    ) -> Optional[Verse]:
        """Find a verse by its reference.

        Args:
            book_name: Book name or abbreviation.
            chapter: Chapter number.
            verse: Verse number.
            translation_abbrev: Translation abbreviation (default: NIV).

        Returns:
            Verse object or None if not found.
        """
        # Try to find the book by abbreviation or name
        book_query = select(Book).where(
            (Book.abbreviation == book_name)
            | (Book.name == book_name)
            | (Book.name_korean == book_name)
        )
        book = self.db.execute(book_query).scalar_one_or_none()

        if not book:
            logger.debug(f"Book not found: {book_name}")
            return None

        # Find the verse
        verse_query = (
            select(Verse)
            .join(Verse.translation)
            .where(
                and_(
                    Verse.book_id == book.id,
                    Verse.chapter == chapter,
                    Verse.verse == verse,
                )
            )
        )

        verse_obj = self.db.execute(verse_query).scalar_one_or_none()
        return verse_obj

    def create_cross_reference(
        self,
        from_verse: Verse,
        to_verse: Verse,
        relationship_type: str,
        confidence: Optional[float] = None,
    ) -> Optional[CrossReference]:
        """Create a cross-reference between two verses.

        Args:
            from_verse: Source verse.
            to_verse: Target verse.
            relationship_type: Type of relationship.
            confidence: Confidence score (0-1).

        Returns:
            Created CrossReference or None if already exists.
        """
        # Check if cross-reference already exists
        existing = (
            self.db.query(CrossReference)
            .filter(
                and_(
                    CrossReference.verse_id == from_verse.id,
                    CrossReference.related_verse_id == to_verse.id,
                    CrossReference.relationship_type == relationship_type,
                )
            )
            .first()
        )

        if existing:
            logger.debug(
                f"Cross-reference already exists: {from_verse.id} -> {to_verse.id}"
            )
            return None

        # Create new cross-reference
        cross_ref = CrossReference(
            verse_id=from_verse.id,
            related_verse_id=to_verse.id,
            relationship_type=relationship_type,
            confidence=confidence,
        )

        self.db.add(cross_ref)
        return cross_ref

    async def populate_from_openbible(
        self,
        translation_abbrev: str = "NIV",
        relationship_type: str = "parallel",
        confidence: float = 0.9,
    ) -> int:
        """Populate cross-references from OpenBible.info data.

        Args:
            translation_abbrev: Translation to use for verse lookup.
            relationship_type: Default relationship type.
            confidence: Default confidence score.

        Returns:
            Number of cross-references created.
        """
        data = await self.fetch_openbible_data()

        created_count = 0
        skipped_count = 0

        for entry in data:
            # Parse source verse
            from_ref = entry.get("from")
            to_refs = entry.get("to", [])

            if not from_ref or not to_refs:
                continue

            from_parsed = self.parse_verse_reference(from_ref)
            if not from_parsed:
                skipped_count += 1
                continue

            from_book, from_chapter, from_verse_num = from_parsed
            from_verse = self.find_verse_by_reference(
                from_book, from_chapter, from_verse_num, translation_abbrev
            )

            if not from_verse:
                skipped_count += 1
                continue

            # Process each target verse
            for to_ref in to_refs:
                to_parsed = self.parse_verse_reference(to_ref)
                if not to_parsed:
                    continue

                to_book, to_chapter, to_verse_num = to_parsed
                to_verse = self.find_verse_by_reference(
                    to_book, to_chapter, to_verse_num, translation_abbrev
                )

                if not to_verse:
                    continue

                # Create bidirectional cross-references
                cross_ref = self.create_cross_reference(
                    from_verse, to_verse, relationship_type, confidence
                )
                if cross_ref:
                    created_count += 1

                # Create reverse reference
                reverse_ref = self.create_cross_reference(
                    to_verse, from_verse, relationship_type, confidence
                )
                if reverse_ref:
                    created_count += 1

            # Commit in batches of 100
            if created_count % 100 == 0 and created_count > 0:
                self.db.commit()
                logger.info(f"Created {created_count} cross-references so far...")

        # Final commit
        self.db.commit()

        logger.info(
            f"Cross-reference population complete: {created_count} created, {skipped_count} skipped"
        )
        return created_count

    def generate_semantic_cross_references(
        self,
        verse_id: UUID,
        similarity_threshold: float = 0.85,
        max_results: int = 10,
    ) -> List[CrossReference]:
        """Generate cross-references based on semantic similarity.

        Args:
            verse_id: Source verse ID.
            similarity_threshold: Minimum similarity score (0-1).
            max_results: Maximum number of cross-references to generate.

        Returns:
            List of created CrossReference objects.
        """
        # This would use the embedding similarity search
        # For now, return empty list (to be implemented with vector search)
        logger.warning("Semantic cross-reference generation not yet implemented")
        return []

    def get_cross_references(
        self, verse_id: UUID, relationship_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get cross-references for a verse.

        Args:
            verse_id: Verse ID.
            relationship_types: Filter by relationship types.

        Returns:
            List of cross-reference dictionaries with verse details.
        """
        query = (
            self.db.query(CrossReference)
            .filter(CrossReference.verse_id == verse_id)
        )

        if relationship_types:
            query = query.filter(CrossReference.relationship_type.in_(relationship_types))

        cross_refs = query.all()

        results = []
        for ref in cross_refs:
            related_verse = ref.related_verse
            results.append(
                {
                    "verse_id": str(related_verse.id),
                    "book": related_verse.book.name,
                    "book_korean": related_verse.book.name_korean,
                    "chapter": related_verse.chapter,
                    "verse": related_verse.verse,
                    "text": related_verse.text,
                    "relationship_type": ref.relationship_type,
                    "confidence": ref.confidence,
                }
            )

        return results


async def main():
    """Main function for populating cross-references."""
    import asyncio

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    manager = CrossReferenceManager()

    try:
        logger.info("Starting cross-reference population from OpenBible.info...")
        count = await manager.populate_from_openbible()
        logger.info(f"Successfully created {count} cross-references!")
    except Exception as e:
        logger.error(f"Error populating cross-references: {e}")
        raise
    finally:
        manager.db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
