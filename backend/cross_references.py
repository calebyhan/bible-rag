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

    # Cross-reference data from scrollmapper/bible_databases (OpenBible.info source)
    # Data is split into 7 files (0-6) for size management
    CROSS_REF_BASE_URL = "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/sources/extras/cross_references_{}.json"
    CROSS_REF_FILE_COUNT = 7  # Files numbered 0 through 6

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
        """Fetch cross-reference data from scrollmapper/bible_databases.

        The data is split into multiple files (0-6) for size management.

        Returns:
            List of cross-reference dictionaries.

        Raises:
            httpx.HTTPError: If fetching data fails.
        """
        logger.info("Fetching cross-reference data from scrollmapper/bible_databases...")

        all_cross_refs = []

        async with httpx.AsyncClient(timeout=120.0) as client:
            for i in range(self.CROSS_REF_FILE_COUNT):
                url = self.CROSS_REF_BASE_URL.format(i)
                logger.info(f"Fetching file {i+1}/{self.CROSS_REF_FILE_COUNT}: {url}")

                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                # Extract cross_references array from each file
                cross_refs = data.get("cross_references", [])
                all_cross_refs.extend(cross_refs)
                logger.info(f"  Loaded {len(cross_refs)} entries from file {i}")

        logger.info(f"Fetched {len(all_cross_refs)} total cross-references")
        return all_cross_refs

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

        # Find the translation
        from database import Translation
        translation_query = select(Translation).where(
            Translation.abbreviation == translation_abbrev
        )
        translation = self.db.execute(translation_query).scalar_one_or_none()

        if not translation:
            logger.debug(f"Translation not found: {translation_abbrev}")
            return None

        # Find the verse
        verse_query = select(Verse).where(
            and_(
                Verse.translation_id == translation.id,
                Verse.book_id == book.id,
                Verse.chapter == chapter,
                Verse.verse == verse,
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
    ) -> int:
        """Populate cross-references from scrollmapper/bible_databases (OpenBible.info source).

        The new data format is:
        {
            "from_verse": {"book": "Genesis", "chapter": 1, "verse": 1},
            "to_verse": [
                {"book": "Proverbs", "chapter": 8, "verse_start": 22, "verse_end": 22}
            ],
            "votes": 59
        }

        Args:
            translation_abbrev: Translation to use for verse lookup.
            relationship_type: Default relationship type.

        Returns:
            Number of cross-references created.
        """
        data = await self.fetch_openbible_data()

        created_count = 0
        skipped_count = 0
        # Track added cross-references to avoid duplicates within the batch
        added_refs = set()

        for entry in data:
            # Parse source verse
            from_verse_data = entry.get("from_verse")
            to_verse_list = entry.get("to_verse", [])
            votes = entry.get("votes", 0)

            if not from_verse_data or not to_verse_list:
                continue

            # Calculate confidence based on votes (normalize to 0-1 range)
            # Positive votes indicate agreement/confidence
            # Negative votes indicate disagreement/low confidence
            # votes typically range from -31 to 100+
            # Map to 0-1 range: negative votes → 0-0.5, positive votes → 0.5-1.0
            if votes < 0:
                # Negative votes: map -100 to 0, and -1 to ~0.49
                confidence = max(0.0, 0.5 + (votes / 200.0))
            else:
                # Positive votes: map 0 to 0.5, 100+ to 1.0
                confidence = min(0.5 + (votes / 200.0), 1.0)

            # Find source verse
            from_verse = self.find_verse_by_reference(
                from_verse_data["book"],
                from_verse_data["chapter"],
                from_verse_data["verse"],
                translation_abbrev,
            )

            if not from_verse:
                skipped_count += 1
                continue

            # Process each target verse
            for to_verse_data in to_verse_list:
                # Handle verse ranges (verse_start to verse_end)
                verse_start = to_verse_data.get("verse_start")
                verse_end = to_verse_data.get("verse_end", verse_start)

                # For now, just use the start verse (could expand to handle ranges)
                to_verse = self.find_verse_by_reference(
                    to_verse_data["book"],
                    to_verse_data["chapter"],
                    verse_start,
                    translation_abbrev,
                )

                if not to_verse:
                    continue

                # Create unique key for tracking
                forward_key = (from_verse.id, to_verse.id, relationship_type)
                reverse_key = (to_verse.id, from_verse.id, relationship_type)

                # Create bidirectional cross-references (skip if already added)
                if forward_key not in added_refs:
                    cross_ref = self.create_cross_reference(
                        from_verse, to_verse, relationship_type, confidence
                    )
                    if cross_ref:
                        created_count += 1
                        added_refs.add(forward_key)

                # Create reverse reference (skip if already added)
                if reverse_key not in added_refs:
                    reverse_ref = self.create_cross_reference(
                        to_verse, from_verse, relationship_type, confidence
                    )
                    if reverse_ref:
                        created_count += 1
                        added_refs.add(reverse_key)

            # Commit in batches of 1000
            if created_count % 1000 == 0 and created_count > 0:
                try:
                    self.db.commit()
                    logger.info(f"Created {created_count} cross-references so far...")
                except Exception as e:
                    logger.warning(f"Batch commit failed (likely duplicates), rolling back: {e}")
                    self.db.rollback()

        # Final commit
        try:
            self.db.commit()
        except Exception as e:
            logger.warning(f"Final commit failed (likely duplicates), rolling back: {e}")
            self.db.rollback()

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
