"""Test Hebrew Bible fetcher from OSHB."""

import sys
from pathlib import Path

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_fetchers import fetch_wlc_hebrew

def test_hebrew_fetcher():
    """Test fetching a single book from OSHB."""

    print("=" * 70)
    print("TESTING HEBREW BIBLE FETCHER (OSHB)")
    print("=" * 70)

    # Temporarily modify the function to test just Ruth (smallest book)
    print("\n📥 Fetching Hebrew Bible data from OSHB...")
    print("Testing with Ruth (smallest OT book)...\n")

    verses_data = fetch_wlc_hebrew()

    if not verses_data:
        print("❌ No data fetched!")
        return

    print(f"\n✅ Successfully fetched {len(verses_data):,} verses")

    # Show sample data from Ruth 1:1
    print("\n" + "=" * 70)
    print("SAMPLE DATA: Ruth 1:1")
    print("=" * 70)

    ruth_1_1 = next((v for v in verses_data if v['book'] == 'Ruth' and v['chapter'] == 1 and v['verse'] == 1), None)

    if ruth_1_1:
        print(f"\nBook: {ruth_1_1['book']}")
        print(f"Chapter: {ruth_1_1['chapter']}")
        print(f"Verse: {ruth_1_1['verse']}")
        print(f"Words: {len(ruth_1_1['words'])}")
        print("\nWord-by-word analysis:")
        print("-" * 70)

        for i, word_data in enumerate(ruth_1_1['words'][:5], 1):  # Show first 5 words
            print(f"\n{i}. {word_data['word']}")
            print(f"   Strong's: {word_data.get('strongs', 'N/A')}")
            print(f"   Morphology: {word_data.get('morphology', 'N/A')}")
            print(f"   Order: {word_data.get('word_order', 'N/A')}")

        if len(ruth_1_1['words']) > 5:
            print(f"\n   ... and {len(ruth_1_1['words']) - 5} more words")

    # Show summary statistics
    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)

    total_words = sum(len(v['words']) for v in verses_data)
    books = set(v['book'] for v in verses_data)

    print(f"\nTotal verses: {len(verses_data):,}")
    print(f"Total words: {total_words:,}")
    print(f"Books fetched: {len(books)}")
    print(f"Books: {', '.join(sorted(books)[:5])}...")

    # Check Strong's coverage
    words_with_strongs = sum(1 for v in verses_data for w in v['words'] if w.get('strongs'))
    strongs_coverage = (words_with_strongs / total_words * 100) if total_words > 0 else 0

    print(f"\nWords with Strong's numbers: {words_with_strongs:,} ({strongs_coverage:.1f}%)")

    print("\n" + "=" * 70)
    print("✅ HEBREW FETCHER TEST COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    test_hebrew_fetcher()
