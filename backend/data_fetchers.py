"""Fetchers for downloading Bible data from free online sources.

This module provides functions to download complete Bible translations
from public domain and free API sources.
"""

import json
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


def fetch_from_api_bible(api_key: str, bible_id: str) -> list[dict]:
    """Fetch Bible from scripture.api.bible (API.Bible).

    Requires API key from https://scripture.api.bible

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


# Translation mappings
TRANSLATION_FETCHERS = {
    "KJV": fetch_kjv,
    "WEB": fetch_web,
    "RKV": fetch_korean,  # Korean Revised Version
}


def fetch_translation(abbreviation: str, api_key: Optional[str] = None) -> list[dict]:
    """Fetch a Bible translation by abbreviation.

    Args:
        abbreviation: Translation abbreviation (e.g., 'KJV', 'NIV', 'RKV')
        api_key: Optional API key for API.Bible (required for NIV, ESV, etc.)

    Returns:
        List of verse dictionaries
    """
    fetcher = TRANSLATION_FETCHERS.get(abbreviation)

    if fetcher:
        return fetcher()
    elif api_key and abbreviation in ["NIV", "ESV", "NASB"]:
        # Map to API.Bible IDs
        bible_ids = {
            "NIV": "de4e12af7f28f599-02",  # NIV 2011
            "ESV": "f421fe261da7624f-01",  # ESV
            "NASB": "65eec8e0b60e656b-01",  # NASB
        }
        bible_id = bible_ids.get(abbreviation)
        if bible_id:
            return fetch_from_api_bible(api_key, bible_id)

    print(f"No fetcher available for {abbreviation}")
    return []
