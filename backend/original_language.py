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

import requests
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from database import Book, OriginalWord, SessionLocal, Verse

# httpx is optional - only needed for async version
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


class OriginalLanguageManager:
    """Manages original language word data for Bible verses."""

    # Strong's concordance data sources (JavaScript format, not JSON)
    STRONGS_HEBREW_URL = "https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongs-hebrew-dictionary.js"
    STRONGS_GREEK_URL = "https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongs-greek-dictionary.js"

    # Fallback: .dat file format (simple text-based)
    STRONGS_GREEK_DAT_URL = "https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongsgreek.dat"
    STRONGS_HEBREW_DAT_URL = "https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongshebrew.dat"

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

    def _parse_js_dictionary(self, js_text: str) -> Dict:
        """Parse JavaScript dictionary format to Python dict.

        The data format is:
        var strongsGreekDictionary = {"G1615": {...}, ...};
        module.exports = strongsGreekDictionary;

        Some entries may have problematic characters, so we use a robust approach.

        Args:
            js_text: JavaScript source code containing dictionary.

        Returns:
            Parsed dictionary.
        """
        import re

        # Find the start of the dictionary object
        dict_start = js_text.find('= {')
        if dict_start == -1:
            logger.error("Could not find dictionary start")
            return {}

        # Find the end - look for "}; module.exports" or similar
        dict_end = js_text.rfind('};')
        if dict_end == -1:
            logger.error("Could not find dictionary end")
            return {}

        # Extract the JSON object (including the braces)
        json_str = js_text[dict_start + 2:dict_end + 1]  # +2 to skip "= ", +1 to include final }

        # Parse as JSON with error recovery
        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON at position {e.pos}: {e.msg}")
            # Try to identify the problematic entry
            lines = json_str[:e.pos].split('\n')
            logger.error(f"Error near line {len(lines)}: {lines[-1] if lines else 'unknown'}")
            return {}

    def _parse_dat_format(self, dat_text: str, language: str) -> Dict:
        """Parse Strong's .dat file format to dictionary.

        The format is:
        $$T0005598
        \\05598\\
         5598  omega  o'-meg-ah

         the last letter of the Greek alphabet, i.e. (figuratively) the
         finality:--Omega.

        Args:
            dat_text: .dat file content
            language: "greek" or "hebrew" for prefix

        Returns:
            Dictionary mapping Strong's numbers to definitions
        """
        prefix = "G" if language == "greek" else "H"
        strongs_dict = {}

        # Split into entries using $$T marker
        entries = re.split(r'\$\$T0+', dat_text)

        for entry in entries:
            if not entry.strip():
                continue

            lines = entry.strip().split('\n')
            if not lines:
                continue

            # First line after $$T is the number
            first_line = lines[0]

            # Look for number pattern like \05598\ or just 5598
            number_match = re.search(r'\\?0*(\d{1,5})\\?', first_line)
            if not number_match:
                continue

            strongs_number = prefix + number_match.group(1)

            # Parse the definition line (format: " 5598  lemma  transliteration")
            lemma = ""
            translit = ""
            definition_lines = []

            found_lemma_line = False
            for i, line in enumerate(lines):
                # Skip the number line
                if i == 0:
                    continue

                stripped = line.strip()
                if not stripped:
                    continue

                # Look for line with: number lemma transliteration
                # Example: " 8600  tphowtsah  tef-o-tsaw'"
                if not found_lemma_line and re.match(r'^\s*\d+\s+\S+\s+\S', line):
                    parts = stripped.split(None, 2)  # Split on whitespace, max 3 parts
                    if len(parts) >= 3:
                        # parts[0] is number, parts[1] is lemma, parts[2] is transliteration
                        lemma = parts[1]
                        translit = parts[2]
                        found_lemma_line = True
                    continue

                # Skip "see GREEK" / "see HEBREW" references
                if stripped.startswith('see GREEK') or stripped.startswith('see HEBREW'):
                    continue

                # Everything else is definition
                definition_lines.append(stripped)

            # Combine definition lines
            definition = ' '.join(definition_lines).strip()

            # Only add if we have a definition
            if definition:
                strongs_dict[strongs_number] = {
                    "lemma": lemma,
                    "translit": translit,
                    "strongs_def": definition,
                    "kjv_def": definition  # Same as definition for .dat format
                }

        logger.info(f"Parsed {len(strongs_dict)} entries from .dat file")
        return strongs_dict

    async def fetch_strongs_data(self) -> tuple[Dict, Dict]:
        """Fetch Strong's concordance data from GitHub (async version).

        Tries JavaScript format first, falls back to .dat format if unavailable.

        Returns:
            Tuple of (hebrew_data, greek_data) dictionaries.

        Raises:
            httpx.HTTPError: If fetching data fails.
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for async operations. Use fetch_strongs_data_sync() instead.")

        logger.info("Fetching Strong's concordance data...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Try Hebrew data - JavaScript first, then .dat
            hebrew_data = {}
            try:
                logger.info(f"Fetching Hebrew data from {self.STRONGS_HEBREW_URL}")
                hebrew_response = await client.get(self.STRONGS_HEBREW_URL)
                hebrew_response.raise_for_status()
                hebrew_data = self._parse_js_dictionary(hebrew_response.text)
            except Exception as e:
                logger.warning(f"Failed to fetch Hebrew JS format: {e}")
                logger.info(f"Trying .dat format: {self.STRONGS_HEBREW_DAT_URL}")
                try:
                    hebrew_dat_response = await client.get(self.STRONGS_HEBREW_DAT_URL)
                    hebrew_dat_response.raise_for_status()
                    hebrew_data = self._parse_dat_format(hebrew_dat_response.text, "hebrew")
                except Exception as dat_error:
                    logger.error(f"Failed to fetch Hebrew .dat format: {dat_error}")

            # Try Greek data - JavaScript first, then .dat
            greek_data = {}
            try:
                logger.info(f"Fetching Greek data from {self.STRONGS_GREEK_URL}")
                greek_response = await client.get(self.STRONGS_GREEK_URL)
                greek_response.raise_for_status()
                greek_data = self._parse_js_dictionary(greek_response.text)
            except Exception as e:
                logger.warning(f"Failed to fetch Greek JS format: {e}")
                logger.info(f"Trying .dat format: {self.STRONGS_GREEK_DAT_URL}")
                try:
                    greek_dat_response = await client.get(self.STRONGS_GREEK_DAT_URL)
                    greek_dat_response.raise_for_status()
                    greek_data = self._parse_dat_format(greek_dat_response.text, "greek")
                except Exception as dat_error:
                    logger.error(f"Failed to fetch Greek .dat format: {dat_error}")

        logger.info(
            f"Fetched {len(hebrew_data)} Hebrew entries and {len(greek_data)} Greek entries"
        )

        self.strongs_hebrew_data = hebrew_data
        self.strongs_greek_data = greek_data

        return hebrew_data, greek_data

    def fetch_strongs_data_sync(self) -> tuple[Dict, Dict]:
        """Fetch Strong's concordance data synchronously (for use in scripts).

        Tries JavaScript format first, falls back to .dat format if unavailable.

        Returns:
            Tuple of (hebrew_data, greek_data) dictionaries.
        """
        logger.info("Fetching Strong's concordance data (synchronous)...")

        # Try Hebrew data - .dat format
        hebrew_data = {}
        try:
            logger.info(f"Fetching Hebrew .dat from {self.STRONGS_HEBREW_DAT_URL}")
            hebrew_response = requests.get(self.STRONGS_HEBREW_DAT_URL, timeout=60)
            hebrew_response.raise_for_status()
            hebrew_data = self._parse_dat_format(hebrew_response.text, "hebrew")
        except Exception as e:
            logger.error(f"Failed to fetch Hebrew .dat format: {e}")

        # Try Greek data - .dat format
        greek_data = {}
        try:
            logger.info(f"Fetching Greek .dat from {self.STRONGS_GREEK_DAT_URL}")
            greek_response = requests.get(self.STRONGS_GREEK_DAT_URL, timeout=60)
            greek_response.raise_for_status()
            greek_data = self._parse_dat_format(greek_response.text, "greek")
        except Exception as e:
            logger.error(f"Failed to fetch Greek .dat format: {e}")

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

        The data format from openscriptures/strongs is:
        {
            "strongs_def": " to love (in a social or moral sense)",
            "kjv_def": "(be-)love(-ed)",
            "lemma": "ἀγαπάω",
            "translit": "agapáō",
            "derivation": "..."
        }

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

        data = self.strongs_greek_data if language == "greek" else self.strongs_hebrew_data

        # The key includes the G/H prefix in the new format
        return data.get(strongs_number)

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
                # Use strongs_def (primary definition) or kjv_def as fallback
                definition = strongs_data.get("strongs_def") or strongs_data.get("kjv_def")
                if not transliteration:
                    transliteration = strongs_data.get("translit")
                # Could also extract lemma (original script word)
                if not word:
                    word = strongs_data.get("lemma", "")

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

    def populate_greek_nt(self, verses_data: list[dict], batch_size: int = 100) -> int:
        """Populate Greek New Testament original words from OpenGNT data.

        Args:
            verses_data: List of verse dictionaries from fetch_opengnt()
            batch_size: Number of verses to commit at once

        Returns:
            Number of words created
        """
        from tqdm import tqdm

        logger.info(f"Populating Greek NT with {len(verses_data)} verses...")

        # Load Strong's definitions if not already loaded
        if not self.strongs_greek_data:
            logger.info("Loading Strong's Greek definitions...")
            self.fetch_strongs_data_sync()

        total_words = 0
        batch = []

        for verse_data in tqdm(verses_data, desc="Populating Greek NT"):
            # Find the verse in the database
            book_query = select(Book).where(Book.book_number == verse_data["book_number"])
            book = self.db.execute(book_query).scalar_one_or_none()

            if not book:
                logger.warning(f"Book {verse_data['book_number']} not found")
                continue

            verse_query = (
                select(Verse)
                .where(Verse.book_id == book.id)
                .where(Verse.chapter == verse_data["chapter"])
                .where(Verse.verse == verse_data["verse"])
                .limit(1)  # Get first matching verse (works across all translations)
            )
            verse = self.db.execute(verse_query).scalars().first()

            if not verse:
                logger.warning(
                    f"Verse not found: Book {verse_data['book_number']}, "
                    f"Chapter {verse_data['chapter']}, Verse {verse_data['verse']}"
                )
                continue

            # Add each word from this verse
            for word_data in verse_data["words"]:
                # Get Strong's definition if available
                definition = None
                if word_data.get("strongs"):
                    strongs_data = self.get_strongs_definition(word_data["strongs"], "greek")
                    if strongs_data:
                        definition = strongs_data.get("strongs_def") or strongs_data.get("kjv_def")

                original_word = OriginalWord(
                    verse_id=verse.id,
                    word=word_data["text"],
                    language="greek",
                    strongs_number=word_data.get("strongs"),
                    transliteration=word_data.get("transliteration"),
                    morphology=word_data.get("morphology"),
                    definition=definition,
                    word_order=word_data.get("word_order", 0),
                )

                batch.append(original_word)
                total_words += 1

                # Commit in batches
                if len(batch) >= batch_size:
                    self.db.add_all(batch)
                    self.db.commit()
                    batch = []

        # Commit remaining words
        if batch:
            self.db.add_all(batch)
            self.db.commit()

        logger.info(f"✅ Created {total_words} Greek words")
        return total_words

    def populate_hebrew_ot(self, verses_data: list[dict], batch_size: int = 100) -> int:
        """Populate Hebrew Old Testament original words from WLC/OSHB data.

        Args:
            verses_data: List of verse dictionaries from fetch_wlc_hebrew()
            batch_size: Number of verses to commit at once

        Returns:
            Number of words created
        """
        from tqdm import tqdm

        logger.info(f"Populating Hebrew OT with {len(verses_data)} verses...")

        # Load Strong's definitions if not already loaded
        if not self.strongs_hebrew_data:
            logger.info("Loading Strong's Hebrew definitions...")
            self.fetch_strongs_data_sync()

        total_words = 0
        batch = []

        for verse_data in tqdm(verses_data, desc="Populating Hebrew OT"):
            # Find the verse in the database using book name
            book_name = verse_data.get("book")
            if not book_name:
                logger.warning(f"Missing book name in verse data")
                continue

            book_query = select(Book).where(Book.name == book_name)
            book = self.db.execute(book_query).scalar_one_or_none()

            if not book:
                logger.warning(f"Book '{book_name}' not found in database")
                continue

            verse_query = (
                select(Verse)
                .where(Verse.book_id == book.id)
                .where(Verse.chapter == verse_data["chapter"])
                .where(Verse.verse == verse_data["verse"])
                .limit(1)  # Get first matching verse (works across all translations)
            )
            verse = self.db.execute(verse_query).scalars().first()

            if not verse:
                logger.warning(
                    f"Verse not found: {book_name} {verse_data['chapter']}:{verse_data['verse']}"
                )
                continue

            # Determine language (Hebrew or Aramaic)
            # Note: Daniel and Ezra have some Aramaic portions
            language = verse_data.get("language", "hebrew")

            # Add each word from this verse
            for word_data in verse_data["words"]:
                # Get Strong's definition and transliteration if available
                definition = None
                transliteration = word_data.get("transliteration")  # From WLC if available
                strongs_num = word_data.get("strongs")

                if strongs_num:
                    strongs_data = self.get_strongs_definition(strongs_num, "hebrew")
                    if strongs_data:
                        definition = strongs_data.get("strongs_def") or strongs_data.get("kjv_def")
                        # Use Strong's transliteration if WLC doesn't provide one
                        if not transliteration:
                            transliteration = strongs_data.get("translit")

                original_word = OriginalWord(
                    verse_id=verse.id,
                    word=word_data.get("word"),
                    language=language,
                    strongs_number=strongs_num,
                    transliteration=transliteration,
                    morphology=word_data.get("morphology"),
                    definition=definition,
                    word_order=word_data.get("word_order", 0),
                )

                batch.append(original_word)
                total_words += 1

                # Commit in batches
                if len(batch) >= batch_size:
                    self.db.add_all(batch)
                    self.db.commit()
                    batch = []

        # Commit remaining words
        if batch:
            self.db.add_all(batch)
            self.db.commit()

        logger.info(f"✅ Created {total_words} Hebrew/Aramaic words")
        return total_words

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
