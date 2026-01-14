"""Fetchers for downloading Bible data from free online sources.

This module provides functions to download complete Bible translations
from public domain and free API sources.
"""

import json
import re
import time
from typing import Optional

import requests
from tqdm import tqdm

from data.books_metadata import BOOKS_METADATA


def fetch_from_getbible(translation_code: str) -> list[dict]:
    """Fetch Bible data from GetBible API.

    Supports multiple translations including:
    - kjv: King James Version (English)
    - web: World English Bible (English)
    - korean: Korean Revised Version (개역성경)

    Args:
        translation_code: Translation code (e.g., 'kjv', 'web', 'korean')

    Returns:
        List of verse dictionaries with keys:
            - book_number: int (1-66)
            - chapter: int
            - verse: int
            - text: str
    """
    base_url = "https://api.getbible.net/v2"
    verses_data = []

    print(f"Fetching {translation_code} from GetBible API...")

    # Mapping of book names to book numbers
    book_name_to_number = {}
    for book_meta in BOOKS_METADATA:
        book_name_to_number[book_meta.name.lower()] = book_meta.book_number
        book_name_to_number[book_meta.abbreviation.lower()] = book_meta.book_number

    try:
        # Fetch books list
        books_url = f"{base_url}/{translation_code}/books.json"
        print(f"Fetching books list from: {books_url}")
        response = requests.get(books_url, timeout=30)
        response.raise_for_status()
        books_data = response.json()

        # GetBible returns a dict with book numbers as keys
        # Convert to list of book info dicts
        if isinstance(books_data, dict):
            books_list = list(books_data.values())
        else:
            books_list = books_data

        # Iterate through each book
        for book_info in tqdm(books_list, desc=f"Downloading {translation_code}"):
            book_nr = book_info.get("nr")
            book_name = book_info.get("name", "").lower()

            # Try to find book number from our metadata
            book_number = book_nr

            # Fetch all chapters for this book
            book_url = f"{base_url}/{translation_code}/{book_nr}.json"
            time.sleep(0.1)  # Rate limiting

            try:
                book_response = requests.get(book_url, timeout=30)
                book_response.raise_for_status()
                book_json = book_response.json()

                chapters = book_json.get("chapters", [])

                for chapter_data in chapters:
                    chapter_nr = chapter_data.get("chapter")
                    verses = chapter_data.get("verses", [])

                    for verse_data in verses:
                        verse_nr = verse_data.get("verse")
                        text = verse_data.get("text", "")

                        # Clean HTML tags if present
                        import re
                        text = re.sub(r'<[^>]+>', '', text)

                        verses_data.append({
                            "book_number": book_number,
                            "chapter": chapter_nr,
                            "verse": verse_nr,
                            "text": text.strip(),
                        })

            except requests.RequestException as e:
                print(f"Error fetching book {book_nr}: {e}")
                continue

    except requests.RequestException as e:
        print(f"Error fetching books list: {e}")
        return []

    print(f"Fetched {len(verses_data)} verses from GetBible")
    return verses_data


def fetch_from_bible_supesearch(filename: str) -> list[dict]:
    """Fetch Bible data from Bible SuperSearch JSON files.

    Downloads complete Bible from SourceForge.

    Args:
        filename: Filename like 'kjv.json' or 'korean.json'

    Returns:
        List of verse dictionaries
    """
    # Determine language folder
    if 'korean' in filename.lower():
        lang_folder = 'KO-Korean'
    else:
        lang_folder = 'EN-English'

    url = f"https://sourceforge.net/projects/biblesuper/files/All%20Bibles%20-%20JSON/{lang_folder}/{filename}/download"

    print(f"Fetching {filename} from Bible SuperSearch...")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=60, allow_redirects=True)
        response.raise_for_status()

        bible_data = response.json()
        verses_data = []

        # Parse Bible SuperSearch format
        # Format varies - implement based on actual structure
        # This is a placeholder - adjust based on actual file structure

        print(f"Downloaded {filename}, parsing...")

        # TODO: Implement parsing based on actual Bible SuperSearch JSON structure
        # This will depend on the format they use

        return verses_data

    except requests.RequestException as e:
        print(f"Error fetching from Bible SuperSearch: {e}")
        return []


def fetch_kjv() -> list[dict]:
    """Fetch King James Version (public domain).

    Returns:
        List of verse dictionaries
    """
    return fetch_from_getbible("kjv")


def fetch_web() -> list[dict]:
    """Fetch World English Bible (public domain).

    Returns:
        List of verse dictionaries
    """
    return fetch_from_getbible("web")


def fetch_korean() -> list[dict]:
    """Fetch Korean Revised Version (개역성경).

    Returns:
        List of verse dictionaries
    """
    return fetch_from_getbible("korean")


def fetch_nkrv(sql_file_path: Optional[str] = None) -> list[dict]:
    """Fetch 개역개정 (New Korean Revised Version).

    ⚠️ COPYRIGHT NOTICE:
    개역개정 is copyrighted by 대한성서공회 (Korean Bible Society).
    For EDUCATIONAL and NON-COMMERCIAL use only.

    Requires bible2_1.sql file downloaded from:
    https://sir.kr/g5_tip/4160

    Args:
        sql_file_path: Path to bible2_1.sql file (defaults to ./bible2_1.sql)

    Returns:
        List of verse dictionaries
    """
    from fetch_nkrv import fetch_nkrv as fetch_nkrv_impl
    return fetch_nkrv_impl(sql_file_path)


def fetch_from_bolls(translation_code: str) -> list[dict]:
    """Fetch Bible data from Bolls.life API (free, unlimited).

    Supports 100+ translations including:
    - NIV, NIV2011: New International Version
    - ESV: English Standard Version
    - NASB: New American Standard Bible
    - KRV: 개역한글 (Korean Revised Version)
    - RNKSV: 새번역 (New Korean Revised Standard Version)

    Args:
        translation_code: Translation code (e.g., 'NIV', 'ESV', 'NASB', 'KRV')

    Returns:
        List of verse dictionaries with keys:
            - book_number: int (1-66)
            - chapter: int
            - verse: int
            - text: str
    """
    base_url = "https://bolls.life"
    verses_data = []

    print(f"Fetching {translation_code} from Bolls.life API...")

    # Fetch books list with retry logic
    books_data = None
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            books_url = f"{base_url}/get-books/{translation_code}/"
            print(f"Fetching books list from: {books_url}")
            response = requests.get(books_url, timeout=60)
            response.raise_for_status()
            books_data = response.json()
            break  # Success

        except (requests.Timeout, requests.RequestException) as e:
            if attempt < max_retries - 1:
                print(f"⏳ Retry {attempt + 1}/{max_retries} for books list (timeout/error)")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"❌ Failed to fetch books list after {max_retries} retries: {e}")
                return []

    if books_data is None:
        return []

    try:

        # Iterate through each book
        for book_info in tqdm(books_data, desc=f"Downloading {translation_code}"):
            book_number = book_info.get("bookid")  # 1-66
            book_name = book_info.get("name")
            num_chapters = book_info.get("chapters")  # Number of chapters (int)

            # Skip if no chapters
            if not num_chapters:
                continue

            # Fetch each chapter (1 to num_chapters)
            for chapter_nr in range(1, num_chapters + 1):
                # Fetch verses for this chapter
                verse_url = f"{base_url}/get-chapter/{translation_code}/{book_number}/{chapter_nr}/"
                time.sleep(0.1)  # Rate limiting

                # Retry logic with exponential backoff
                max_retries = 3
                retry_delay = 1
                verse_data = None

                for attempt in range(max_retries):
                    try:
                        verse_response = requests.get(verse_url, timeout=60)  # Increased timeout to 60s
                        verse_response.raise_for_status()
                        verse_data = verse_response.json()
                        break  # Success, exit retry loop

                    except (requests.Timeout, requests.RequestException) as e:
                        if attempt < max_retries - 1:
                            print(f"\n  ⏳ Retry {attempt + 1}/{max_retries} for {book_name} {chapter_nr}")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            print(f"\n  ❌ Failed after {max_retries} retries: {book_name} {chapter_nr}: {e}")
                            verse_data = None
                            break

                # Skip if we couldn't fetch the data
                if verse_data is None:
                    continue

                # Parse verses
                for verse in verse_data:
                    verse_nr = verse.get("verse")
                    text = verse.get("text", "")

                    # Clean HTML tags from Bolls.life text
                    # Remove <br/>, <br>, and other common HTML tags
                    text = re.sub(r'<br\s*/?>|<p>|</p>|<i>|</i>|<b>|</b>', ' ', text)
                    text = re.sub(r'<[^>]+>', '', text)  # Remove any remaining HTML tags
                    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

                    verses_data.append({
                        "book_number": book_number,
                        "chapter": chapter_nr,
                        "verse": verse_nr,
                        "text": text.strip(),
                    })

    except requests.RequestException as e:
        print(f"Error fetching books list: {e}")
        return []

    print(f"Fetched {len(verses_data)} verses from Bolls.life")
    return verses_data


def fetch_from_api_bible(api_key: str, bible_id: str) -> list[dict]:
    """Fetch Bible from scripture.api.bible (API.Bible).

    Requires API key from https://scripture.api.bible
    NOTE: Consider using Bolls.life API instead for free access to NIV, ESV, NASB.

    Args:
        api_key: API.Bible API key
        bible_id: Bible ID (e.g., 'de4e12af7f28f599-02' for NIV)

    Returns:
        List of verse dictionaries
    """
    base_url = "https://api.scripture.api.bible/v1"
    headers = {"api-key": api_key}
    verses_data = []

    print(f"Fetching Bible {bible_id} from API.Bible...")

    try:
        # Get books list
        books_url = f"{base_url}/bibles/{bible_id}/books"
        response = requests.get(books_url, headers=headers, timeout=30)
        response.raise_for_status()
        books = response.json()["data"]

        for book in tqdm(books, desc="Downloading"):
            book_id = book["id"]

            # Get chapters for this book
            chapters_url = f"{base_url}/bibles/{bible_id}/books/{book_id}/chapters"
            time.sleep(0.2)  # Rate limiting

            chapters_response = requests.get(chapters_url, headers=headers, timeout=30)
            chapters_response.raise_for_status()
            chapters = chapters_response.json()["data"]

            for chapter in chapters:
                chapter_id = chapter["id"]

                # Get verses for this chapter
                verses_url = f"{base_url}/bibles/{bible_id}/chapters/{chapter_id}/verses"
                time.sleep(0.2)  # Rate limiting

                verses_response = requests.get(verses_url, headers=headers, timeout=30)
                verses_response.raise_for_status()
                verses = verses_response.json()["data"]

                for verse in verses:
                    # Parse verse reference
                    reference = verse["reference"]
                    text = verse["text"]

                    # Extract book number, chapter, verse from reference
                    # This is simplified - you'd need better parsing
                    parts = reference.split()
                    if len(parts) >= 2:
                        verse_ref = parts[-1].split(":")
                        if len(verse_ref) == 2:
                            chapter_nr = int(verse_ref[0])
                            verse_nr = int(verse_ref[1])

                            # Find book number from book_id
                            # This requires mapping - simplified here
                            book_number = 1  # TODO: Implement proper mapping

                            verses_data.append({
                                "book_number": book_number,
                                "chapter": chapter_nr,
                                "verse": verse_nr,
                                "text": text.strip(),
                            })

    except requests.RequestException as e:
        print(f"Error fetching from API.Bible: {e}")
        return []

    print(f"Fetched {len(verses_data)} verses")
    return verses_data


# Translation mappings for public domain sources (GetBible)
GETBIBLE_FETCHERS = {
    "KJV": fetch_kjv,
    "WEB": fetch_web,
    "RKV": fetch_korean,  # Korean Revised Version (개역성경)
}

# Translation requiring manual SQL file (educational use only)
MANUAL_FETCHERS = {
    "NKRV": fetch_nkrv,  # 개역개정 (educational use only)
}

# Translation codes for Bolls.life API (free, unlimited)
# These are available without API keys
BOLLS_TRANSLATIONS = {
    "NIV": "NIV",           # New International Version 1984
    "NIV2011": "NIV2011",   # New International Version 2011
    "ESV": "ESV",           # English Standard Version
    "NASB": "NASB",         # New American Standard Bible
    "KJV": "KJV",           # King James Version (also on GetBible)
    "NKJV": "NKJV",         # New King James Version
    "NLT": "NLT",           # New Living Translation
    "WEB": "WEB",           # World English Bible (also on GetBible)
    "KRV": "KRV",           # 개역한글 (Korean Revised Version)
    "RNKSV": "RNKSV",       # 새번역 (New Korean Revised Standard Version)
}


def fetch_translation(abbreviation: str, api_key: Optional[str] = None) -> list[dict]:
    """Fetch a Bible translation by abbreviation.

    Tries multiple sources in order:
    1. GetBible API (public domain only: KJV, WEB, RKV)
    2. Bolls.life API (free, 100+ translations including NIV, ESV, NASB, Korean)
    3. Manual fetchers (NKRV - requires SQL file)
    4. API.Bible (requires API key - not recommended due to rate limits)

    Args:
        abbreviation: Translation abbreviation (e.g., 'KJV', 'NIV', 'ESV', 'KRV', 'NKRV')
        api_key: Optional API key for API.Bible (not needed for Bolls.life)

    Returns:
        List of verse dictionaries
    """
    # Try GetBible first (public domain, reliable)
    if abbreviation in GETBIBLE_FETCHERS:
        print(f"Using GetBible API for {abbreviation}")
        return GETBIBLE_FETCHERS[abbreviation]()

    # Try Bolls.life (free, supports 100+ translations)
    if abbreviation in BOLLS_TRANSLATIONS:
        print(f"Using Bolls.life API for {abbreviation}")
        bolls_code = BOLLS_TRANSLATIONS[abbreviation]
        return fetch_from_bolls(bolls_code)

    # Try manual fetchers (requires downloaded files)
    if abbreviation in MANUAL_FETCHERS:
        print(f"Using manual fetcher for {abbreviation}")
        print("⚠️  Educational/non-commercial use only")
        return MANUAL_FETCHERS[abbreviation]()

    # Fallback to API.Bible if API key provided
    if api_key and abbreviation in ["NIV", "ESV", "NASB"]:
        print(f"Using API.Bible for {abbreviation} (requires API key)")
        bible_ids = {
            "NIV": "de4e12af7f28f599-02",  # NIV 2011
            "ESV": "f421fe261da7624f-01",  # ESV
            "NASB": "65eec8e0b60e656b-01",  # NASB
        }
        bible_id = bible_ids.get(abbreviation)
        if bible_id:
            return fetch_from_api_bible(api_key, bible_id)

    print(f"No fetcher available for {abbreviation}")
    available = list(GETBIBLE_FETCHERS.keys()) + list(BOLLS_TRANSLATIONS.keys()) + list(MANUAL_FETCHERS.keys())
    print(f"Available translations: {available}")
    return []
