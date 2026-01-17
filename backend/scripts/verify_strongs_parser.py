"""Test Strong's .dat parser."""

import sys
from pathlib import Path

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from original_language import OriginalLanguageManager


def test_strongs_parser():
    """Test parsing Strong's .dat files and fetching definitions."""

    print("=" * 70)
    print("TESTING STRONG'S .DAT PARSER")
    print("=" * 70)

    mgr = OriginalLanguageManager()

    print("\n📥 Fetching Strong's data from .dat files...")
    hebrew_data, greek_data = mgr.fetch_strongs_data_sync()

    print(f"\n✅ Successfully loaded:")
    print(f"   Hebrew entries: {len(hebrew_data):,}")
    print(f"   Greek entries: {len(greek_data):,}")

    # Test Greek definitions
    print("\n📖 Testing Greek definitions:")
    print("-" * 70)

    test_greek_numbers = ["G25", "G2316", "G3588", "G2889"]
    for strongs_num in test_greek_numbers:
        definition = mgr.get_strongs_definition(strongs_num, "greek")
        if definition:
            print(f"\n{strongs_num}: {definition.get('lemma', 'N/A')}")
            print(f"  Transliteration: {definition.get('translit', 'N/A')}")
            print(f"  Definition: {definition.get('strongs_def', 'N/A')[:80]}...")
        else:
            print(f"\n{strongs_num}: ❌ Not found")

    # Test Hebrew definitions
    print("\n\n📖 Testing Hebrew definitions:")
    print("-" * 70)

    test_hebrew_numbers = ["H430", "H776", "H8064", "H1254"]
    for strongs_num in test_hebrew_numbers:
        definition = mgr.get_strongs_definition(strongs_num, "hebrew")
        if definition:
            print(f"\n{strongs_num}: {definition.get('lemma', 'N/A')}")
            print(f"  Transliteration: {definition.get('translit', 'N/A')}")
            print(f"  Definition: {definition.get('strongs_def', 'N/A')[:80]}...")
        else:
            print(f"\n{strongs_num}: ❌ Not found")

    print("\n" + "=" * 70)
    print("✅ STRONG'S PARSER TEST COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    test_strongs_parser()
