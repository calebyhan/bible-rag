"""Run complete original language ingestion for the entire Bible (NT + OT + Aramaic).

This script:
1. Fetches complete Greek NT from OpenGNT (all 27 books, ~7,941 verses)
2. Fetches complete Hebrew OT from OSHB (all 39 books, ~23,213 verses)
3. Identifies and marks Aramaic portions in Daniel, Ezra, Jeremiah, Genesis
4. Populates original_words table with Greek/Hebrew/Aramaic text, Strong's numbers, morphology
5. Reports statistics and verification
"""

import sys
import time
from pathlib import Path

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_fetchers import fetch_opengnt, fetch_wlc_hebrew
from database import SessionLocal, Book, Verse, OriginalWord, Translation, init_db
from original_language import OriginalLanguageManager
from sqlalchemy import func

# Define Aramaic verse ranges
ARAMAIC_PORTIONS = {
    'Daniel': [
        # Daniel 2:4b-7:28
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
    """Check if a verse is in an Aramaic portion of the Bible."""
    if book_name not in ARAMAIC_PORTIONS:
        return False

    for portion in ARAMAIC_PORTIONS[book_name]:
        if (portion['chapter'] == chapter and
            portion['verse_start'] <= verse <= portion['verse_end']):
            return True

    return False


def mark_aramaic_portions(hebrew_verses: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separate Hebrew verses into Hebrew and Aramaic portions.

    Args:
        hebrew_verses: All verses from OSHB

    Returns:
        Tuple of (hebrew_only_verses, aramaic_verses)
    """
    hebrew_only = []
    aramaic = []

    for verse_data in hebrew_verses:
        book_name = verse_data.get('book')
        chapter = verse_data.get('chapter')
        verse_num = verse_data.get('verse')

        if is_aramaic_verse(book_name, chapter, verse_num):
            # Mark as Aramaic
            verse_data['language'] = 'aramaic'
            aramaic.append(verse_data)
        else:
            # Keep as Hebrew
            verse_data['language'] = 'hebrew'
            hebrew_only.append(verse_data)

    return hebrew_only, aramaic


def run_complete_ingestion():
    """Execute complete original language ingestion for NT + OT."""

    print("=" * 80)
    print("COMPLETE BIBLE ORIGINAL LANGUAGE INGESTION (NT + OT)")
    print("=" * 80)

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

        # Check for NT verses (books 40-66)
        nt_verse_count = db.query(Verse).join(Book).filter(
            Book.book_number.between(40, 66)
        ).count()
        print(f"   NT verses in database: {nt_verse_count:,}")

        # Check for OT verses (books 1-39)
        ot_verse_count = db.query(Verse).join(Book).filter(
            Book.book_number.between(1, 39)
        ).count()
        print(f"   OT verses in database: {ot_verse_count:,}")

        if nt_verse_count == 0:
            print("\n⚠️ WARNING: No NT verses found! Greek ingestion will be skipped.")
        if ot_verse_count == 0:
            print("\n⚠️ WARNING: No OT verses found! Hebrew ingestion will be skipped.")

        orig_lang_mgr = OriginalLanguageManager(db)

        # =========================
        # PART 1: GREEK NEW TESTAMENT
        # =========================
        greek_word_count = 0
        if nt_verse_count > 0:
            print("\n" + "=" * 80)
            print("PART 1: GREEK NEW TESTAMENT")
            print("=" * 80)

            print("\n📖 Step 3: Fetching Greek New Testament (OpenGNT)...")
            greek_verses = fetch_opengnt()

            if not greek_verses:
                print("❌ Failed to fetch OpenGNT data")
            else:
                print(f"   ✅ Fetched {len(greek_verses):,} verses from OpenGNT")

                # Clear existing Greek words
                print("\n🗑️  Step 4: Clearing existing Greek original words...")
                existing_greek = db.query(OriginalWord).filter(
                    OriginalWord.language == 'greek'
                ).count()
                print(f"   Found {existing_greek:,} existing Greek words")

                if existing_greek > 0:
                    print("   Deleting and re-ingesting...")
                    db.query(OriginalWord).filter(
                        OriginalWord.language == 'greek'
                    ).delete(synchronize_session=False)
                    db.commit()
                    print(f"   ✅ Deleted {existing_greek:,} existing Greek words")

                # Populate Greek words
                print("\n⚡ Step 5: Populating Greek original words...")
                print(f"   Processing {len(greek_verses):,} verses...")

                greek_word_count = orig_lang_mgr.populate_greek_nt(greek_verses, batch_size=100)
                print(f"   ✅ Created {greek_word_count:,} Greek words")

        # =========================
        # PART 2: HEBREW OLD TESTAMENT + ARAMAIC
        # =========================
        hebrew_word_count = 0
        aramaic_word_count = 0
        if ot_verse_count > 0:
            print("\n" + "=" * 80)
            print("PART 2: HEBREW OLD TESTAMENT + ARAMAIC")
            print("=" * 80)

            print("\n📖 Step 6: Fetching Hebrew Old Testament (OSHB)...")
            all_ot_verses = fetch_wlc_hebrew()

            if not all_ot_verses:
                print("❌ Failed to fetch OSHB data")
            else:
                print(f"   ✅ Fetched {len(all_ot_verses):,} verses from OSHB")

                # Separate Hebrew and Aramaic portions
                print("\n🔍 Step 7: Identifying Aramaic portions...")
                hebrew_verses, aramaic_verses = mark_aramaic_portions(all_ot_verses)
                print(f"   Hebrew verses: {len(hebrew_verses):,}")
                print(f"   Aramaic verses: {len(aramaic_verses):,}")

                if aramaic_verses:
                    print(f"\n   Aramaic portions identified:")
                    aramaic_books = {}
                    for v in aramaic_verses:
                        book = v['book']
                        aramaic_books[book] = aramaic_books.get(book, 0) + 1
                    for book, count in sorted(aramaic_books.items()):
                        print(f"     • {book}: {count} verses")

                # Clear existing Hebrew words
                print("\n🗑️  Step 8: Clearing existing Hebrew original words...")
                existing_hebrew = db.query(OriginalWord).filter(
                    OriginalWord.language == 'hebrew'
                ).count()
                print(f"   Found {existing_hebrew:,} existing Hebrew words")

                if existing_hebrew > 0:
                    print("   Deleting and re-ingesting...")
                    db.query(OriginalWord).filter(
                        OriginalWord.language == 'hebrew'
                    ).delete(synchronize_session=False)
                    db.commit()
                    print(f"   ✅ Deleted {existing_hebrew:,} existing Hebrew words")

                # Clear existing Aramaic words
                print("\n🗑️  Step 9: Clearing existing Aramaic original words...")
                existing_aramaic = db.query(OriginalWord).filter(
                    OriginalWord.language == 'aramaic'
                ).count()
                print(f"   Found {existing_aramaic:,} existing Aramaic words")

                if existing_aramaic > 0:
                    print("   Deleting and re-ingesting...")
                    db.query(OriginalWord).filter(
                        OriginalWord.language == 'aramaic'
                    ).delete(synchronize_session=False)
                    db.commit()
                    print(f"   ✅ Deleted {existing_aramaic:,} existing Aramaic words")

                # Populate Hebrew words
                print("\n⚡ Step 10: Populating Hebrew original words...")
                print(f"   Processing {len(hebrew_verses):,} verses...")

                hebrew_word_count = orig_lang_mgr.populate_hebrew_ot(hebrew_verses, batch_size=100)
                print(f"   ✅ Created {hebrew_word_count:,} Hebrew words")

                # Populate Aramaic words
                if aramaic_verses:
                    print("\n⚡ Step 11: Populating Aramaic original words...")
                    print(f"   Processing {len(aramaic_verses):,} verses...")

                    aramaic_word_count = orig_lang_mgr.populate_hebrew_ot(aramaic_verses, batch_size=100)
                    print(f"   ✅ Created {aramaic_word_count:,} Aramaic words")

        # =========================
        # FINAL STATISTICS
        # =========================
        elapsed = time.time() - start_time
        total_word_count = greek_word_count + hebrew_word_count + aramaic_word_count

        print("\n" + "=" * 80)
        print("✅ COMPLETE INGESTION FINISHED!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"   Greek NT words: {greek_word_count:,}")
        print(f"   Hebrew OT words: {hebrew_word_count:,}")
        print(f"   Aramaic words: {aramaic_word_count:,}")
        print(f"   Total words created: {total_word_count:,}")
        print(f"   Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        if total_word_count > 0:
            print(f"   Speed: {total_word_count/elapsed:.0f} words/second")

        # =========================
        # VERIFICATION
        # =========================
        print("\n" + "=" * 80)
        print("🔍 VERIFICATION")
        print("=" * 80)

        # Greek verification
        print("\n📖 Greek New Testament:")
        total_greek = db.query(OriginalWord).filter(
            OriginalWord.language == 'greek'
        ).count()
        greek_with_strongs = db.query(OriginalWord).filter(
            OriginalWord.language == 'greek',
            OriginalWord.strongs_number.isnot(None)
        ).count()
        greek_with_def = db.query(OriginalWord).filter(
            OriginalWord.language == 'greek',
            OriginalWord.definition.isnot(None),
            OriginalWord.definition != ''
        ).count()

        print(f"   Total words: {total_greek:,}")
        if total_greek > 0:
            print(f"   With Strong's numbers: {greek_with_strongs:,} ({greek_with_strongs/total_greek*100:.1f}%)")
            print(f"   With definitions: {greek_with_def:,} ({greek_with_def/total_greek*100:.1f}%)")

        # Hebrew verification
        print("\n📖 Hebrew Old Testament:")
        total_hebrew = db.query(OriginalWord).filter(
            OriginalWord.language == 'hebrew'
        ).count()
        hebrew_with_strongs = db.query(OriginalWord).filter(
            OriginalWord.language == 'hebrew',
            OriginalWord.strongs_number.isnot(None)
        ).count()
        hebrew_with_def = db.query(OriginalWord).filter(
            OriginalWord.language == 'hebrew',
            OriginalWord.definition.isnot(None),
            OriginalWord.definition != ''
        ).count()

        print(f"   Total words: {total_hebrew:,}")
        if total_hebrew > 0:
            print(f"   With Strong's numbers: {hebrew_with_strongs:,} ({hebrew_with_strongs/total_hebrew*100:.1f}%)")
            print(f"   With definitions: {hebrew_with_def:,} ({hebrew_with_def/total_hebrew*100:.1f}%)")

        # Aramaic verification
        print("\n📖 Aramaic Portions:")
        total_aramaic = db.query(OriginalWord).filter(
            OriginalWord.language == 'aramaic'
        ).count()
        aramaic_with_strongs = db.query(OriginalWord).filter(
            OriginalWord.language == 'aramaic',
            OriginalWord.strongs_number.isnot(None)
        ).count()
        aramaic_with_def = db.query(OriginalWord).filter(
            OriginalWord.language == 'aramaic',
            OriginalWord.definition.isnot(None),
            OriginalWord.definition != ''
        ).count()

        print(f"   Total words: {total_aramaic:,}")
        if total_aramaic > 0:
            print(f"   With Strong's numbers: {aramaic_with_strongs:,} ({aramaic_with_strongs/total_aramaic*100:.1f}%)")
            print(f"   With definitions: {aramaic_with_def:,} ({aramaic_with_def/total_aramaic*100:.1f}%)")

            # Show Aramaic book distribution
            aramaic_books = db.query(
                Book.name,
                func.count(OriginalWord.id).label('word_count')
            ).join(Verse, Verse.book_id == Book.id).join(
                OriginalWord, OriginalWord.verse_id == Verse.id
            ).filter(
                OriginalWord.language == 'aramaic'
            ).group_by(Book.name).all()

            if aramaic_books:
                print(f"\n   Distribution by book:")
                for book_name, word_count in aramaic_books:
                    print(f"     • {book_name}: {word_count:,} words")

        # Sample verses
        print("\n📖 Sample Verse Verification:")

        # Genesis 1:1 (Hebrew)
        gen_1_1 = db.query(Verse).join(Book).filter(
            Book.book_number == 1,
            Verse.chapter == 1,
            Verse.verse == 1
        ).first()

        if gen_1_1:
            gen_words = db.query(OriginalWord).filter(
                OriginalWord.verse_id == gen_1_1.id
            ).order_by(OriginalWord.word_order).all()

            if gen_words:
                print(f"\n   Genesis 1:1 ({len(gen_words)} Hebrew words):")
                hebrew_text = " ".join([w.word for w in gen_words])
                print(f"   Hebrew: {hebrew_text}")
                print(f"   First 3 words:")
                for i, word in enumerate(gen_words[:3], 1):
                    translit = word.transliteration or "N/A"
                    strongs = word.strongs_number or "N/A"
                    definition = (word.definition[:40] + "...") if word.definition and len(word.definition) > 40 else (word.definition or "N/A")
                    print(f"     {i}. {word.word} ({translit}) - {strongs}")
                    print(f"        {definition}")

        # John 3:16 (Greek)
        john_3_16 = db.query(Verse).join(Book).filter(
            Book.book_number == 43,
            Verse.chapter == 3,
            Verse.verse == 16
        ).first()

        if john_3_16:
            john_words = db.query(OriginalWord).filter(
                OriginalWord.verse_id == john_3_16.id
            ).order_by(OriginalWord.word_order).all()

            if john_words:
                print(f"\n   John 3:16 ({len(john_words)} Greek words):")
                greek_text = " ".join([w.word for w in john_words])
                print(f"   Greek: {greek_text[:80]}...")
                print(f"   First 3 words:")
                for i, word in enumerate(john_words[:3], 1):
                    translit = word.transliteration or "N/A"
                    strongs = word.strongs_number or "N/A"
                    definition = (word.definition[:40] + "...") if word.definition and len(word.definition) > 40 else (word.definition or "N/A")
                    print(f"     {i}. {word.word} ({translit}) - {strongs}")
                    print(f"        {definition}")

        # Daniel 2:4 (Aramaic)
        if total_aramaic > 0:
            daniel_2_4 = db.query(Verse).join(Book).filter(
                Book.name == 'Daniel',
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
                    aramaic_text = " ".join([w.word for w in daniel_words])
                    print(f"   Aramaic: {aramaic_text[:80]}...")
                    print(f"   First 3 words:")
                    for i, word in enumerate(daniel_words[:3], 1):
                        translit = word.transliteration or "N/A"
                        strongs = word.strongs_number or "N/A"
                        definition = (word.definition[:40] + "...") if word.definition and len(word.definition) > 40 else (word.definition or "N/A")
                        print(f"     {i}. {word.word} ({translit}) - {strongs}")
                        print(f"        {definition}")

        print("\n" + "=" * 80)
        print("✅ COMPLETE INGESTION SUCCESSFUL!")
        print("=" * 80)
        print(f"\nNext steps:")
        print(f"  1. Test API endpoints with include_original=true")
        print(f"  2. Verify frontend display for OT (Hebrew/Aramaic) and NT (Greek)")
        print(f"  3. Test Aramaic display in Daniel and Ezra")
        print(f"  4. Generate embeddings if needed: python embeddings.py")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = run_complete_ingestion()
    sys.exit(0 if success else 1)
