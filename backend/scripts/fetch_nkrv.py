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
from bs4 import BeautifulSoup
from tqdm import tqdm

from data.books_metadata import BOOKS_METADATA


def fetch_nkrv_from_mysql_dump(sql_file_path: str) -> list[dict]:
    """Parse 개역개정 from MySQL dump file.

    The SQL file from sir.kr contains INSERT statements with Bible verses.
    Expected format:
        INSERT INTO bible VALUES (book_id, chapter, verse, text);

    Args:
        sql_file_path: Path to bible2_1.sql file

    Returns:
        List of verse dictionaries with keys:
            - book_number: int (1-66)
            - chapter: int
            - verse: int
            - text: str
    """
    verses_data = []

    print(f"Parsing MySQL dump from {sql_file_path}...")

    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all INSERT statements
        # Pattern: INSERT INTO `bible` VALUES (book, chapter, verse, 'text');
        insert_pattern = r"INSERT INTO .+? VALUES\s*\((.+?)\);"

        matches = re.findall(insert_pattern, content, re.DOTALL)

        for match in tqdm(matches, desc="Parsing SQL"):
            # Parse individual values
            # Format: book_number, chapter, verse, 'text'
            values = match.split(',', 3)  # Split into max 4 parts

            if len(values) >= 4:
                try:
                    book_number = int(values[0].strip())
                    chapter = int(values[1].strip())
                    verse = int(values[2].strip())

                    # Extract text (remove quotes)
                    text = values[3].strip()
                    # Remove leading/trailing quotes
                    text = re.sub(r"^['\"]|['\"]$", '', text)
                    # Unescape quotes
                    text = text.replace("\\'", "'").replace('\\"', '"')

                    verses_data.append({
                        "book_number": book_number,
                        "chapter": chapter,
                        "verse": verse,
                        "text": text.strip(),
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error parsing line: {e}")
                    continue

    except FileNotFoundError:
        print(f"File not found: {sql_file_path}")
        print("Please download from: https://sir.kr/g5_tip/4160")
        return []
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        return []

    print(f"Parsed {len(verses_data)} verses from SQL dump")
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
    1. Parse existing SQL file
    2. Download SQL file from sir.kr
    3. Return empty list with instructions

    Args:
        sql_file_path: Path to bible2_1.sql (optional)

    Returns:
        List of verse dictionaries
    """
    # Default SQL file path
    if sql_file_path is None:
        sql_file_path = "bible2_1.sql"

    # Try to parse existing file
    import os
    if os.path.exists(sql_file_path):
        print(f"Found existing SQL file: {sql_file_path}")
        return fetch_nkrv_from_mysql_dump(sql_file_path)

    # Try to download
    print(f"SQL file not found, attempting download...")
    if download_nkrv_sql_file(sql_file_path):
        return fetch_nkrv_from_mysql_dump(sql_file_path)

    # Failed
    print("\n⚠️ Unable to fetch 개역개정 automatically.")
    print("\nManual steps:")
    print("1. Visit: https://sir.kr/g5_tip/4160")
    print("2. Download bible2_1.sql (6.0MB)")
    print(f"3. Place in backend/ directory as: {sql_file_path}")
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
