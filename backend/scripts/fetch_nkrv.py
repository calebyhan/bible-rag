"""Fetch 개역개정 (NKRV) Bible data from various sources.

⚠️ COPYRIGHT NOTICE:
개역개정 is copyrighted by 대한성서공회 (Korean Bible Society).
This is for EDUCATIONAL and NON-COMMERCIAL use only.
For commercial use, please obtain official license from KBS.

Sources:
1. MySQL database from sir.kr (community-shared)
2. Web scraping from holybible.or.kr (last resort)
"""

import re
import sys
import time
from pathlib import Path
from typing import Optional

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from tqdm import tqdm

from data.books_metadata import BOOKS_METADATA


def fetch_nkrv_from_mysql_dump(sql_file_path: str) -> list[dict]:
    """Parse 개역개정 from MySQL dump file.

    The SQL file from sir.kr contains INSERT statements with Bible verses.
    Expected format:
        INSERT INTO `bible2` VALUES
        (idx, cate, book, chapter, paragraph, 'sentence', 'testament', 'long_label', 'short_label');

    Args:
        sql_file_path: Path to bible2_1.sql or bible2 1.sql file

    Returns:
        List of verse dictionaries with keys:
            - book_number: int (1-66)
            - chapter: int
            - verse: int (paragraph number)
            - text: str (sentence)
    """
    verses_data = []

    print(f"Parsing MySQL dump from {sql_file_path}...")

    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all INSERT statements for bible2 table
        # Pattern matches INSERT statements with column names
        # Each INSERT may contain multiple value tuples
        # More flexible pattern to handle various whitespace/newline combinations
        insert_pattern = r"INSERT INTO `bible2`[^V]*VALUES\s*([^;]+);"

        matches = re.findall(insert_pattern, content, re.MULTILINE | re.DOTALL)

        print(f"Found {len(matches)} INSERT statement blocks")

        all_tuples = []
        for match_block in matches:
            # Split individual value tuples
            # Pattern: (idx, cate, book, chapter, paragraph, 'sentence', 'testament', 'long_label', 'short_label')
            # Note: sentence can contain single quotes (escaped as '')
            tuple_pattern = r"\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*'([^']*(?:''[^']*)*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)"

            tuples = re.findall(tuple_pattern, match_block)
            all_tuples.extend(tuples)

        print(f"Found {len(all_tuples)} total verses to parse")

        # Use dict to deduplicate by (book, chapter, verse)
        verses_dict = {}

        for tuple_data in tqdm(all_tuples, desc="Parsing verses"):
            try:
                idx = int(tuple_data[0])
                cate = int(tuple_data[1])
                book = int(tuple_data[2])
                chapter = int(tuple_data[3])
                paragraph = int(tuple_data[4])
                sentence = tuple_data[5]
                testament = tuple_data[6]
                long_label = tuple_data[7]
                short_label = tuple_data[8]

                # Skip verse 0 (database constraint requires verse >= 1)
                if paragraph == 0:
                    continue

                # Clean text: remove section headers like <천지 창조>
                text = re.sub(r'<[^>]+>\s*', '', sentence)
                # Unescape single quotes
                text = text.replace("''", "'")
                text = text.strip()

                # Skip empty text (section headers only)
                if not text:
                    continue

                # Create unique key
                key = (book, chapter, paragraph)

                # Only keep first occurrence of each verse
                if key not in verses_dict:
                    verses_dict[key] = {
                        "book_number": book,
                        "chapter": chapter,
                        "verse": paragraph,
                        "text": text,
                    }

            except (ValueError, IndexError) as e:
                print(f"Error parsing tuple: {e}")
                continue

        # Convert dict to list
        verses_data = list(verses_dict.values())
        print(f"Parsed {len(verses_data)} unique verses from SQL dump")

    except FileNotFoundError:
        print(f"File not found: {sql_file_path}")
        print("Please download from: https://sir.kr/g5_tip/4160")
        return []
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        import traceback
        traceback.print_exc()
        return []

    return verses_data


def fetch_nkrv_from_web(book_name: str, chapter: int) -> list[dict]:
    """Fetch 개역개정 from holybible.or.kr (web scraping - use as last resort).

    ⚠️ WARNING: This is web scraping and may violate terms of service.
    Use only for educational purposes and with proper rate limiting.

    Args:
        book_name: Korean book name (e.g., "창세기")
        chapter: Chapter number

    Returns:
        List of verse dictionaries for that chapter
    """
    # Map book names to holybible.or.kr book IDs
    # This would need to be populated based on their URL structure
    # Format example: http://www.holybible.or.kr/B_GAE/cgi/bibleftxt.php?VR=GAE&VL=1&CN=1

    # This is a placeholder - actual implementation would require
    # understanding the website's structure
    print("⚠️ Web scraping not implemented - use MySQL dump instead")
    print("Download from: https://sir.kr/g5_tip/4160")
    return []


def download_nkrv_sql_file(output_path: str = "bible2_1.sql") -> bool:
    """Download 개역개정 MySQL dump from sir.kr.

    Args:
        output_path: Where to save the downloaded file

    Returns:
        True if successful, False otherwise
    """
    url = "https://sir.kr/data/file/g5_tip/bible2_1.sql"

    print(f"Downloading 개역개정 from {url}...")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"Downloaded to {output_path} ({len(response.content)} bytes)")
        return True

    except requests.RequestException as e:
        print(f"Download failed: {e}")
        print("Please download manually from: https://sir.kr/g5_tip/4160")
        return False


def fetch_nkrv(sql_file_path: Optional[str] = None) -> list[dict]:
    """Fetch 개역개정 (NKRV) Bible data.

    Tries in order:
    1. Parse existing SQL file (checks multiple paths)
    2. Download SQL file from sir.kr
    3. Return empty list with instructions

    Args:
        sql_file_path: Path to bible2_1.sql or bible2 1.sql (optional)

    Returns:
        List of verse dictionaries
    """
    import os

    # Try multiple possible file paths
    possible_paths = []

    if sql_file_path is not None:
        possible_paths.append(sql_file_path)

    # Common paths to check
    possible_paths.extend([
        "bible2 1.sql",  # File with space
        "bible2_1.sql",  # File with underscore
        "../bible2 1.sql",  # Project root from backend/scripts
        "../bible2_1.sql",
        "../../bible2 1.sql",  # From deeper directories
        "../../bible2_1.sql",
    ])

    # Try to find existing file
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found existing SQL file: {path}")
            return fetch_nkrv_from_mysql_dump(path)

    # Use default path for download attempt
    default_path = sql_file_path or "bible2_1.sql"

    # Try to download
    print(f"SQL file not found, attempting download...")
    if download_nkrv_sql_file(default_path):
        return fetch_nkrv_from_mysql_dump(default_path)

    # Failed
    print("\n⚠️ Unable to fetch 개역개정 automatically.")
    print("\nManual steps:")
    print("1. Visit: https://sir.kr/g5_tip/4160")
    print("2. Download bible2_1.sql (6.0MB)")
    print(f"3. Place in project root or backend/ directory")
    print("4. Run ingestion again")
    print("\nAlternative: Use 개역한글 (KRV) which is copyright-free:")
    print("  python data_ingestion.py  # Already includes KRV")

    return []


if __name__ == "__main__":
    # Test the fetcher
    verses = fetch_nkrv()
    if verses:
        print(f"\n✅ Successfully fetched {len(verses)} verses")
        print("\nSample verses:")
        for verse in verses[:5]:
            print(f"  {verse['book_number']}:{verse['chapter']}:{verse['verse']} - {verse['text'][:50]}...")
    else:
        print("\n❌ Failed to fetch verses")
