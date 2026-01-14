"""Original language (Greek, Hebrew, Aramaic) word data integration.

This module handles:
1. Fetching Strong's concordance data
2. Parsing and storing original language words
3. Integrating morphological data
"""

import json
import logging
import re
from typing import Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from database import Book, OriginalWord, SessionLocal, Verse

logger = logging.getLogger(__name__)


class OriginalLanguageManager:
    """Manages original language word data for Bible verses."""

    # Strong's concordance data sources
    STRONGS_HEBREW_URL = "https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongsHebrew.json"
    STRONGS_GREEK_URL = "https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongsGreek.json"

    def __init__(self, db: Optional[Session] = None):
        """Initialize the original language manager.

        Args:
            db: Database session. If None, creates new session.
        """
        self.db = db or SessionLocal()
        self._should_close_db = db is None
        self.strongs_hebrew_data: Optional[Dict] = None
        self.strongs_greek_data: Optional[Dict] = None

    def __del__(self):
        """Close database session if we created it."""
        if self._should_close_db and self.db:
            self.db.close()

    async def fetch_strongs_data(self) -> tuple[Dict, Dict]:
        """Fetch Strong's concordance data from GitHub.

        Returns:
            Tuple of (hebrew_data, greek_data) dictionaries.

        Raises:
            httpx.HTTPError: If fetching data fails.
        """
        logger.info("Fetching Strong's concordance data...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Fetch Hebrew data
            logger.info(f"Fetching Hebrew data from {self.STRONGS_HEBREW_URL}")
            hebrew_response = await client.get(self.STRONGS_HEBREW_URL)
            hebrew_response.raise_for_status()
            hebrew_data = hebrew_response.json()

            # Fetch Greek data
            logger.info(f"Fetching Greek data from {self.STRONGS_GREEK_URL}")
            greek_response = await client.get(self.STRONGS_GREEK_URL)
            greek_response.raise_for_status()
            greek_data = greek_response.json()

        logger.info(
            f"Fetched {len(hebrew_data)} Hebrew entries and {len(greek_data)} Greek entries"
        )

        self.strongs_hebrew_data = hebrew_data
        self.strongs_greek_data = greek_data

        return hebrew_data, greek_data

    def get_strongs_definition(
        self, strongs_number: str, language: str = "greek"
    ) -> Optional[Dict]:
        """Get Strong's definition for a given number.

        Args:
            strongs_number: Strong's number (e.g., "G25", "H430").
            language: Language ("greek" or "hebrew").

        Returns:
            Dictionary with definition data or None if not found.
        """
        # Ensure data is loaded
        if language == "greek" and not self.strongs_greek_data:
            logger.warning("Greek Strong's data not loaded")
            return None
        if language == "hebrew" and not self.strongs_hebrew_data:
            logger.warning("Hebrew Strong's data not loaded")
            return None

        # Extract number from Strong's reference (remove G/H prefix)
        number = strongs_number.lstrip("GH")

        data = self.strongs_greek_data if language == "greek" else self.strongs_hebrew_data

        return data.get(number)

    def parse_strongs_from_text(self, text: str) -> List[str]:
        """Extract Strong's numbers from text.

        Looks for patterns like G1234, H5678, etc.

        Args:
            text: Text containing Strong's references.

        Returns:
            List of Strong's numbers found.
        """
        pattern = r"\b([GH]\d{1,5})\b"
        matches = re.findall(pattern, text)
        return matches

    def create_original_word(
        self,
        verse: Verse,
        word: str,
        language: str,
        strongs_number: Optional[str] = None,
        transliteration: Optional[str] = None,
        morphology: Optional[str] = None,
        definition: Optional[str] = None,
        word_order: Optional[int] = None,
    ) -> OriginalWord:
        """Create an original language word entry.

        Args:
            verse: Verse object.
            word: Original language word text.
            language: Language ("greek", "hebrew", or "aramaic").
            strongs_number: Strong's concordance number.
            transliteration: Romanized transliteration.
            morphology: Morphological information.
            definition: English definition.
            word_order: Position in verse.

        Returns:
            Created OriginalWord object.
        """
        # Enrich with Strong's data if number provided
        if strongs_number and not definition:
            strongs_data = self.get_strongs_definition(strongs_number, language)
            if strongs_data:
                definition = strongs_data.get("def") or strongs_data.get("strongs_def")
                if not transliteration:
                    transliteration = strongs_data.get("translit")

        original_word = OriginalWord(
            verse_id=verse.id,
            word=word,
            language=language,
            strongs_number=strongs_number,
            transliteration=transliteration,
            morphology=morphology,
            definition=definition,
            word_order=word_order,
        )

        self.db.add(original_word)
        return original_word

    async def populate_from_original_text(
        self, translation_abbrev: str = "SBLGNT"
    ) -> int:
        """Populate original words from original language translation.

        Args:
            translation_abbrev: Translation abbreviation (SBLGNT for Greek, WLC for Hebrew).

        Returns:
            Number of original words created.
        """
        # This would require parsing the actual Greek/Hebrew text
        # and mapping words to Strong's numbers
        # Implementation would depend on the data source format

        logger.warning(
            "Full original text population requires specialized parsing - not yet implemented"
        )
        return 0

    def add_sample_original_words(self) -> int:
        """Add sample original language words for demonstration.

        Returns:
            Number of words created.
        """
        logger.info("Adding sample original language words...")

        # Example: John 3:16 in Greek
        # "οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον..."
        sample_data = [
            {
                "book": "John",
                "chapter": 3,
                "verse": 16,
                "language": "greek",
                "words": [
                    {"word": "οὕτως", "strongs": "G3779", "translit": "houtōs", "order": 1},
                    {"word": "γὰρ", "strongs": "G1063", "translit": "gar", "order": 2},
                    {"word": "ἠγάπησεν", "strongs": "G25", "translit": "ēgapēsen", "order": 3},
                    {"word": "ὁ", "strongs": "G3588", "translit": "ho", "order": 4},
                    {"word": "θεὸς", "strongs": "G2316", "translit": "theos", "order": 5},
                    {"word": "τὸν", "strongs": "G3588", "translit": "ton", "order": 6},
                    {"word": "κόσμον", "strongs": "G2889", "translit": "kosmon", "order": 7},
                ],
            },
            {
                "book": "Genesis",
                "chapter": 1,
                "verse": 1,
                "language": "hebrew",
                "words": [
                    {"word": "בְּרֵאשִׁית", "strongs": "H7225", "translit": "bereshit", "order": 1},
                    {"word": "בָּרָא", "strongs": "H1254", "translit": "bara", "order": 2},
                    {"word": "אֱלֹהִים", "strongs": "H430", "translit": "elohim", "order": 3},
                    {"word": "אֵת", "strongs": "H853", "translit": "et", "order": 4},
                    {"word": "הַשָּׁמַיִם", "strongs": "H8064", "translit": "hashamayim", "order": 5},
                    {"word": "וְאֵת", "strongs": "H853", "translit": "ve'et", "order": 6},
                    {"word": "הָאָרֶץ", "strongs": "H776", "translit": "ha'aretz", "order": 7},
                ],
            },
        ]

        created_count = 0

        for entry in sample_data:
            # Find the verse
            book_query = select(Book).where(Book.name == entry["book"])
            book = self.db.execute(book_query).scalar_one_or_none()

            if not book:
                logger.warning(f"Book not found: {entry['book']}")
                continue

            verse_query = (
                select(Verse)
                .where(
                    and_(
                        Verse.book_id == book.id,
                        Verse.chapter == entry["chapter"],
                        Verse.verse == entry["verse"],
                    )
                )
                .limit(1)
            )

            verse = self.db.execute(verse_query).scalar_one_or_none()

            if not verse:
                logger.warning(
                    f"Verse not found: {entry['book']} {entry['chapter']}:{entry['verse']}"
                )
                continue

            # Add each word
            for word_data in entry["words"]:
                self.create_original_word(
                    verse=verse,
                    word=word_data["word"],
                    language=entry["language"],
                    strongs_number=word_data["strongs"],
                    transliteration=word_data.get("translit"),
                    word_order=word_data.get("order"),
                )
                created_count += 1

        self.db.commit()
        logger.info(f"Created {created_count} sample original language words")
        return created_count

    def get_original_words(self, verse_id: UUID) -> List[Dict]:
        """Get original language words for a verse.

        Args:
            verse_id: Verse ID.

        Returns:
            List of original word dictionaries.
        """
        words = (
            self.db.query(OriginalWord)
            .filter(OriginalWord.verse_id == verse_id)
            .order_by(OriginalWord.word_order)
            .all()
        )

        results = []
        for word in words:
            results.append(
                {
                    "word": word.word,
                    "language": word.language,
                    "strongs_number": word.strongs_number,
                    "transliteration": word.transliteration,
                    "morphology": word.morphology,
                    "definition": word.definition,
                    "word_order": word.word_order,
                }
            )

        return results

    def get_verses_with_strongs(self, strongs_number: str) -> List[Dict]:
        """Find all verses containing a specific Strong's number.

        Args:
            strongs_number: Strong's number to search for.

        Returns:
            List of verse dictionaries.
        """
        words = (
            self.db.query(OriginalWord)
            .filter(OriginalWord.strongs_number == strongs_number)
            .all()
        )

        results = []
        seen_verses = set()

        for word in words:
            if word.verse_id in seen_verses:
                continue

            verse = word.verse
            results.append(
                {
                    "verse_id": str(verse.id),
                    "book": verse.book.name,
                    "book_korean": verse.book.name_korean,
                    "chapter": verse.chapter,
                    "verse": verse.verse,
                    "text": verse.text,
                    "word": word.word,
                    "transliteration": word.transliteration,
                }
            )
            seen_verses.add(word.verse_id)

        return results


async def main():
    """Main function for populating original language data."""
    import asyncio

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    manager = OriginalLanguageManager()

    try:
        logger.info("Fetching Strong's concordance data...")
        await manager.fetch_strongs_data()

        logger.info("Adding sample original language words...")
        count = manager.add_sample_original_words()

        logger.info(f"Successfully created {count} original language words!")
    except Exception as e:
        logger.error(f"Error populating original language data: {e}")
        raise
    finally:
        manager.db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
