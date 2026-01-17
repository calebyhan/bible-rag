"""Sample script for original language ingestion - John only for quick testing."""

import sys
from pathlib import Path

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_fetchers import fetch_opengnt
from database import SessionLocal, Book, Verse, OriginalWord, Translation, init_db
from original_language import OriginalLanguageManager

def test_john_ingestion():
    """Test ingesting just the book of John (book 43)."""

    print("=" * 60)
    print("TESTING ORIGINAL LANGUAGE INGESTION - JOHN ONLY")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    init_db()

    db = SessionLocal()

    try:
        # Fetch OpenGNT data
        print("\n2. Fetching OpenGNT data...")
        all_verses = fetch_opengnt()

        # Filter for John only (book 43)
        john_verses = [v for v in all_verses if v['book_number'] == 43]
        print(f"   Found {len(john_verses)} verses in John")

        # Check if we have verses in the database for John
        print("\n3. Checking database for John verses...")
        book_43 = db.query(Book).filter(Book.book_number == 43).first()
        if not book_43:
            print("   ❌ Book 43 (John) not found in database!")
            print("   Please run regular ingestion first to populate verses")
            return False

        verse_count = db.query(Verse).filter(Verse.book_id == book_43.id).count()
        print(f"   Found {verse_count} verses for John in database")

        if verse_count == 0:
            print("   ❌ No verses found! Please ingest translations first")
            return False

        # Clear existing original words for John
        print("\n4. Clearing existing original words for John...")
        john_verse_ids = [v.id for v in db.query(Verse).filter(Verse.book_id == book_43.id).all()]
        deleted = db.query(OriginalWord).filter(
            OriginalWord.verse_id.in_(john_verse_ids)
        ).delete(synchronize_session=False)
        db.commit()
        print(f"   Deleted {deleted} existing original words")

        # Populate original words
        print("\n5. Populating original words for John...")
        orig_lang_mgr = OriginalLanguageManager(db)
        word_count = orig_lang_mgr.populate_greek_nt(john_verses, batch_size=50)

        print(f"\n✅ SUCCESS! Created {word_count} Greek words for John")

        # Verify sample verses
        print("\n6. Verifying sample verses...")

        # John 1:1
        verse_1_1 = db.query(Verse).filter(
            Verse.book_id == book_43.id,
            Verse.chapter == 1,
            Verse.verse == 1
        ).first()

        if verse_1_1:
            words_1_1 = db.query(OriginalWord).filter(
                OriginalWord.verse_id == verse_1_1.id
            ).order_by(OriginalWord.word_order).all()

            print(f"\n   John 1:1 - {len(words_1_1)} words:")
            for word in words_1_1[:5]:
                print(f"     {word.word} ({word.transliteration}) - {word.strongs_number}")

        # John 3:16
        verse_3_16 = db.query(Verse).filter(
            Verse.book_id == book_43.id,
            Verse.chapter == 3,
            Verse.verse == 16
        ).first()

        if verse_3_16:
            words_3_16 = db.query(OriginalWord).filter(
                OriginalWord.verse_id == verse_3_16.id
            ).order_by(OriginalWord.word_order).all()

            print(f"\n   John 3:16 - {len(words_3_16)} words:")
            for word in words_3_16[:5]:
                print(f"     {word.word} ({word.transliteration}) - {word.strongs_number}")

        # Check GNT pseudo-translation
        print("\n7. Checking GNT pseudo-translation...")
        gnt_translation = db.query(Translation).filter(
            Translation.abbreviation == "GNT"
        ).first()

        if gnt_translation:
            print(f"   ✅ Found GNT translation: {gnt_translation.name}")
            print(f"      Language: {gnt_translation.language_code}")
            print(f"      Is original: {gnt_translation.is_original_language}")
        else:
            print("   ⚠️  GNT translation not found in database")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_john_ingestion()
    sys.exit(0 if success else 1)
