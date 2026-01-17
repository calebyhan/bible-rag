"""Ingest only Aramaic portions of the Old Testament.

This script:
1. Fetches Hebrew/Aramaic OT from OSHB (Westminster Leningrad Codex)
2. Filters for ONLY Aramaic portions (Daniel, Ezra, Jeremiah, Genesis)
3. Populates original_words table with language='aramaic'
4. Reports statistics

Aramaic portions in the Bible:
- Daniel 2:4b-7:28 (chapters 2-7, mostly)
- Ezra 4:8-6:18, 7:12-26
- Jeremiah 10:11 (one verse)
- Genesis 31:47 (two words)
"""

import sys
import time
from pathlib import Path

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_fetchers import fetch_wlc_hebrew
from database import SessionLocal, Book, Verse, OriginalWord, init_db
from original_language import OriginalLanguageManager
from sqlalchemy import select, func

# Define Aramaic verse ranges
ARAMAIC_PORTIONS = {
    'Daniel': [
        # Daniel 2:4b-7:28
        # Note: 2:4 is split - Hebrew starts, Aramaic begins mid-verse
        # We'll include full chapters 2-7 to be safe
        {'chapter': 2, 'verse_start': 4, 'verse_end': 49},
        {'chapter': 3, 'verse_start': 1, 'verse_end': 30},
        {'chapter': 4, 'verse_start': 1, 'verse_end': 37},
        {'chapter': 5, 'verse_start': 1, 'verse_end': 31},
        {'chapter': 6, 'verse_start': 1, 'verse_end': 28},
        {'chapter': 7, 'verse_start': 1, 'verse_end': 28},
    ],
    'Ezra': [
        # Ezra 4:8-6:18
        {'chapter': 4, 'verse_start': 8, 'verse_end': 24},
        {'chapter': 5, 'verse_start': 1, 'verse_end': 17},
        {'chapter': 6, 'verse_start': 1, 'verse_end': 18},
        # Ezra 7:12-26
        {'chapter': 7, 'verse_start': 12, 'verse_end': 26},
    ],
    'Jeremiah': [
        # Jeremiah 10:11 (single verse)
        {'chapter': 10, 'verse_start': 11, 'verse_end': 11},
    ],
    'Genesis': [
        # Genesis 31:47 (contains two Aramaic words)
        {'chapter': 31, 'verse_start': 47, 'verse_end': 47},
    ],
}


def is_aramaic_verse(book_name: str, chapter: int, verse: int) -> bool:
    """Check if a verse is in an Aramaic portion of the Bible.

    Args:
        book_name: Name of the book (e.g., 'Daniel', 'Ezra')
        chapter: Chapter number
        verse: Verse number

    Returns:
        True if this verse is in an Aramaic portion
    """
    if book_name not in ARAMAIC_PORTIONS:
        return False

    for portion in ARAMAIC_PORTIONS[book_name]:
        if (portion['chapter'] == chapter and
            portion['verse_start'] <= verse <= portion['verse_end']):
            return True

    return False


def filter_aramaic_verses(all_hebrew_verses: list[dict], db) -> list[dict]:
    """Filter a list of Hebrew verses to only include Aramaic portions.

    Args:
        all_hebrew_verses: List of verse dictionaries from fetch_wlc_hebrew()
        db: Database session for looking up book numbers

    Returns:
        List of verse dictionaries containing only Aramaic portions with book_number added
    """
    aramaic_verses = []

    # Create a mapping of book names to book numbers
    books = db.query(Book).all()
    book_name_to_number = {book.name: book.book_number for book in books}

    for verse_data in all_hebrew_verses:
        book_name = verse_data['book']
        chapter = verse_data['chapter']
        verse = verse_data['verse']

        if is_aramaic_verse(book_name, chapter, verse):
            # Mark this verse as Aramaic
            verse_data['language'] = 'aramaic'

            # Add book_number for compatibility with populate_hebrew_ot
            verse_data['book_number'] = book_name_to_number.get(book_name)

            if verse_data['book_number'] is None:
                print(f"⚠️ Warning: Could not find book number for {book_name}")
                continue

            aramaic_verses.append(verse_data)

    return aramaic_verses


def run_aramaic_ingestion():
    """Execute Aramaic-only ingestion."""

    print("=" * 70)
    print("ARAMAIC ORIGINAL LANGUAGE INGESTION")
    print("=" * 70)
    print("\nAramaic portions in the Bible:")
    print("  • Daniel 2:4b-7:28 (6 chapters)")
    print("  • Ezra 4:8-6:18, 7:12-26 (3 sections)")
    print("  • Jeremiah 10:11 (1 verse)")
    print("  • Genesis 31:47 (2 words)")
    print()

    start_time = time.time()

    # Initialize database
    print("\n📚 Step 1: Initializing database...")
    init_db()

    db = SessionLocal()

    try:
        # Check prerequisites
        print("\n📊 Step 2: Checking prerequisites...")
        total_verses = db.query(Verse).count()
        print(f"   Total verses in database: {total_verses:,}")

        if total_verses == 0:
            print("\n❌ ERROR: No verses found in database!")
            print("   Please run regular translation ingestion first:")
            print("   python data_ingestion.py")
            return False

        # Check for OT verses (books 1-39)
        ot_books = db.query(Book).filter(Book.book_number.between(1, 39)).all()
        print(f"   OT books in database: {len(ot_books)}/39")

        ot_verse_count = db.query(Verse).join(Book).filter(
            Book.book_number.between(1, 39)
        ).count()
        print(f"   OT verses in database: {ot_verse_count:,}")

        if ot_verse_count == 0:
            print("\n❌ ERROR: No OT verses found!")
            return False

        # Fetch WLC Hebrew/Aramaic data
        print("\n📖 Step 3: Fetching Hebrew OT from OSHB (includes Aramaic)...")
        print("   This will fetch all OT books but we'll filter for Aramaic only")
        all_hebrew_verses = fetch_wlc_hebrew()

        if not all_hebrew_verses:
            print("❌ Failed to fetch WLC data")
            return False

        print(f"   ✅ Fetched {len(all_hebrew_verses):,} total OT verses")

        # Filter for Aramaic portions only
        print("\n🔍 Step 4: Filtering for Aramaic portions...")
        aramaic_verses = filter_aramaic_verses(all_hebrew_verses, db)
        print(f"   ✅ Filtered to {len(aramaic_verses):,} Aramaic verses")

        # Report coverage by book
        print("\n📚 Aramaic verses by book:")
        books_coverage = {}
        for verse in aramaic_verses:
            book_name = verse['book']
            books_coverage[book_name] = books_coverage.get(book_name, 0) + 1

        for book_name in sorted(books_coverage.keys()):
            print(f"     {book_name}: {books_coverage[book_name]:,} verses")

        # Clear existing Aramaic words
        print("\n🗑️  Step 5: Clearing existing Aramaic original words...")
        existing_aramaic = db.query(OriginalWord).filter(
            OriginalWord.language == 'aramaic'
        ).count()
        print(f"   Found {existing_aramaic:,} existing Aramaic words")

        if existing_aramaic > 0:
            print("   Deleting and re-ingesting...")
            deleted = db.query(OriginalWord).filter(
                OriginalWord.language == 'aramaic'
            ).delete(synchronize_session=False)
            db.commit()
            print(f"   ✅ Deleted {deleted:,} existing Aramaic words")

        # Populate original words
        print("\n⚡ Step 6: Populating Aramaic original words...")
        print(f"   Processing {len(aramaic_verses):,} verses...")

        total_words_estimate = sum(len(v['words']) for v in aramaic_verses)
        print(f"   Estimated words: ~{total_words_estimate:,}")

        orig_lang_mgr = OriginalLanguageManager(db)

        # Load Strong's data
        if not orig_lang_mgr.strongs_hebrew_data:
            print("   Loading Strong's Hebrew/Aramaic definitions...")
            orig_lang_mgr.fetch_strongs_data_sync()

        word_count = orig_lang_mgr.populate_hebrew_ot(aramaic_verses, batch_size=100)

        # Calculate statistics
        elapsed = time.time() - start_time
        print(f"\n✅ INGESTION COMPLETE!")
        print(f"   Total words created: {word_count:,}")
        print(f"   Total time: {elapsed:.1f} seconds")
        print(f"   Speed: {word_count/elapsed:.0f} words/second")

        # Verification
        print("\n🔍 Step 7: Verifying data integrity...")

        # Total Aramaic words
        total_aramaic_words = db.query(OriginalWord).filter(
            OriginalWord.language == 'aramaic'
        ).count()
        print(f"   Total Aramaic words in database: {total_aramaic_words:,}")

        # Words with Strong's numbers
        words_with_strongs = db.query(OriginalWord).filter(
            OriginalWord.language == 'aramaic',
            OriginalWord.strongs_number.isnot(None)
        ).count()
        strongs_percentage = (words_with_strongs / total_aramaic_words * 100) if total_aramaic_words > 0 else 0
        print(f"   Words with Strong's numbers: {words_with_strongs:,} ({strongs_percentage:.1f}%)")

        # Words with transliteration
        words_with_translit = db.query(OriginalWord).filter(
            OriginalWord.language == 'aramaic',
            OriginalWord.transliteration.isnot(None)
        ).count()
        translit_percentage = (words_with_translit / total_aramaic_words * 100) if total_aramaic_words > 0 else 0
        print(f"   Words with transliteration: {words_with_translit:,} ({translit_percentage:.1f}%)")

        # Sample verses verification
        print("\n📖 Sample Aramaic Verse Verification:")

        # Daniel 2:4 (famous transition verse: "Then the Chaldeans spoke to the king in Aramaic")
        daniel_book = db.query(Book).filter(Book.name == 'Daniel').first()
        if daniel_book:
            daniel_2_4 = db.query(Verse).filter(
                Verse.book_id == daniel_book.id,
                Verse.chapter == 2,
                Verse.verse == 4
            ).first()

            if daniel_2_4:
                daniel_words = db.query(OriginalWord).filter(
                    OriginalWord.verse_id == daniel_2_4.id,
                    OriginalWord.language == 'aramaic'
                ).order_by(OriginalWord.word_order).all()

                if daniel_words:
                    print(f"\n   Daniel 2:4 ({len(daniel_words)} Aramaic words):")
                    aramaic_text = " ".join([w.word for w in daniel_words[:10]])  # First 10 words
                    print(f"   Aramaic: {aramaic_text}...")
                    print(f"   First 3 words:")
                    for i, word in enumerate(daniel_words[:3], 1):
                        print(f"     {i}. {word.word} ({word.transliteration or 'N/A'}) - {word.strongs_number}")

        # Ezra 4:8
        ezra_book = db.query(Book).filter(Book.name == 'Ezra').first()
        if ezra_book:
            ezra_4_8 = db.query(Verse).filter(
                Verse.book_id == ezra_book.id,
                Verse.chapter == 4,
                Verse.verse == 8
            ).first()

            if ezra_4_8:
                ezra_words = db.query(OriginalWord).filter(
                    OriginalWord.verse_id == ezra_4_8.id,
                    OriginalWord.language == 'aramaic'
                ).order_by(OriginalWord.word_order).all()

                if ezra_words:
                    print(f"\n   Ezra 4:8 ({len(ezra_words)} Aramaic words):")
                    aramaic_text = " ".join([w.word for w in ezra_words[:10]])
                    print(f"   Aramaic: {aramaic_text}...")

        # Coverage by book
        print("\n📚 Aramaic Coverage by Book:")
        aramaic_books_with_words = db.query(
            Book.name,
            Book.book_number,
            func.count(OriginalWord.id).label('word_count')
        ).join(Verse, Verse.book_id == Book.id).join(
            OriginalWord, OriginalWord.verse_id == Verse.id
        ).filter(
            OriginalWord.language == 'aramaic'
        ).group_by(Book.name, Book.book_number).order_by(Book.book_number).all()

        for book_name, book_num, word_count in aramaic_books_with_words:
            print(f"   {book_name:20s}: {word_count:6,} words")

        # Show all original language counts
        print("\n📊 All Original Language Word Counts:")
        lang_counts = db.query(
            OriginalWord.language,
            func.count(OriginalWord.id)
        ).group_by(OriginalWord.language).all()

        for lang, count in lang_counts:
            print(f"   {lang.capitalize():10s}: {count:,} words")

        print("\n" + "=" * 70)
        print("✅ ARAMAIC INGESTION SUCCESSFUL!")
        print("=" * 70)
        print(f"\nAramaic data is now available in the database!")
        print(f"You can now:")
        print(f"  • View Aramaic text in Browse/Compare pages for Daniel/Ezra")
        print(f"  • See Strong's numbers for Aramaic words")
        print(f"  • Search verses by Aramaic word roots")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = run_aramaic_ingestion()
    sys.exit(0 if success else 1)
