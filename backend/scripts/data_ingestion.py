"""Data ingestion script for Bible translations.

This module handles fetching Bible data from various sources and populating
the database with translations, books, and verses.
"""

import sys
import unicodedata
from pathlib import Path
from typing import Optional

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from tqdm import tqdm

from config import get_settings
from data.books_metadata import BOOKS_METADATA, TRANSLATIONS
from database import Book, SessionLocal, Translation, Verse, init_db

settings = get_settings()


def normalize_text(text: str, language: str = "en") -> str:
    """Normalize text for consistent storage.

    - Apply Unicode NFC normalization (especially important for Korean)
    - Strip leading/trailing whitespace
    - Normalize internal whitespace
    """
    # Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)
    # Strip and normalize whitespace
    text = " ".join(text.split())
    return text


def init_translations(db: Session) -> dict[str, Translation]:
    """Initialize translation records in the database.

    Returns a mapping of abbreviation -> Translation object.
    """
    translations_map = {}

    for trans_data in TRANSLATIONS:
        # Check if translation already exists
        existing = (
            db.query(Translation)
            .filter(Translation.abbreviation == trans_data["abbreviation"])
            .first()
        )

        if existing:
            translations_map[trans_data["abbreviation"]] = existing
        else:
            translation = Translation(
                name=trans_data["name"],
                abbreviation=trans_data["abbreviation"],
                language_code=trans_data["language_code"],
                description=trans_data["description"],
                is_original_language=trans_data["is_original_language"],
            )
            db.add(translation)
            translations_map[trans_data["abbreviation"]] = translation

    db.commit()
    print(f"Initialized {len(translations_map)} translations")
    return translations_map


def init_books(db: Session) -> dict[int, Book]:
    """Initialize book records in the database.

    Returns a mapping of book_number -> Book object.
    """
    books_map = {}

    for book_meta in BOOKS_METADATA:
        # Check if book already exists
        existing = (
            db.query(Book).filter(Book.book_number == book_meta.book_number).first()
        )

        if existing:
            books_map[book_meta.book_number] = existing
        else:
            book = Book(
                name=book_meta.name,
                name_korean=book_meta.name_korean,
                name_original=book_meta.name_original,
                abbreviation=book_meta.abbreviation,
                testament=book_meta.testament,
                genre=book_meta.genre,
                book_number=book_meta.book_number,
                total_chapters=book_meta.total_chapters,
            )
            db.add(book)
            books_map[book_meta.book_number] = book

    db.commit()
    print(f"Initialized {len(books_map)} books")
    return books_map


def insert_verses_batch(
    db: Session,
    verses_data: list[dict],
    translation: Translation,
    books_map: dict[int, Book],
    batch_size: int = 500,
) -> int:
    """Insert verses in batches for better performance.

    Args:
        db: Database session
        verses_data: List of verse dictionaries with keys:
            - book_number: int (1-66)
            - chapter: int
            - verse: int
            - text: str
        translation: Translation object
        books_map: Mapping of book_number -> Book object
        batch_size: Number of verses per commit

    Returns:
        Number of verses inserted
    """
    count = 0
    batch = []

    print(f"Inserting {len(verses_data)} verses for {translation.abbreviation}...")
    for verse_data in tqdm(verses_data, desc=f"Inserting {translation.abbreviation}"):
        book = books_map.get(verse_data["book_number"])
        if not book:
            print(f"Warning: Book {verse_data['book_number']} not found")
            continue

        verse = Verse(
            translation_id=translation.id,
            book_id=book.id,
            chapter=verse_data["chapter"],
            verse=verse_data["verse"],
            text=normalize_text(
                verse_data["text"],
                translation.language_code,
            ),
        )
        batch.append(verse)
        count += 1

        if len(batch) >= batch_size:
            db.add_all(batch)
            db.commit()
            batch = []

    # Insert remaining verses
    if batch:
        db.add_all(batch)
        db.commit()

    return count


def load_bible_data(translation_abbrev: str) -> list[dict]:
    """Load complete Bible data from online sources.

    Args:
        translation_abbrev: Translation abbreviation (e.g., 'KJV', 'NIV', 'RKV')

    Returns:
        List of verse dictionaries
    """
    from data_fetchers import fetch_translation

    # Try to fetch from online source
    verses_data = fetch_translation(translation_abbrev)

    if verses_data:
        return verses_data

    # Fall back to sample data if fetching fails
    print(f"Falling back to sample data for {translation_abbrev}")
    return load_sample_verses(translation_abbrev)


def load_sample_verses(translation_abbrev: str) -> list[dict]:
    """Load sample verses for testing (fallback).

    This returns a small sample of verses for development/testing.
    Used as fallback if online fetching fails.
    """
    # Sample verses from John 3 for testing
    sample_verses = {
        "NIV": [
            {"book_number": 43, "chapter": 3, "verse": 1, "text": "Now there was a Pharisee, a man named Nicodemus who was a member of the Jewish ruling council."},
            {"book_number": 43, "chapter": 3, "verse": 2, "text": 'He came to Jesus at night and said, "Rabbi, we know that you are a teacher who has come from God. For no one could perform the signs you are doing if God were not with him."'},
            {"book_number": 43, "chapter": 3, "verse": 3, "text": 'Jesus replied, "Very truly I tell you, no one can see the kingdom of God unless they are born again."'},
            {"book_number": 43, "chapter": 3, "verse": 14, "text": "Just as Moses lifted up the snake in the wilderness, so the Son of Man must be lifted up,"},
            {"book_number": 43, "chapter": 3, "verse": 15, "text": "that everyone who believes may have eternal life in him."},
            {"book_number": 43, "chapter": 3, "verse": 16, "text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."},
            {"book_number": 43, "chapter": 3, "verse": 17, "text": "For God did not send his Son into the world to condemn the world, but to save the world through him."},
            # Matthew 6 - Lord's Prayer and Forgiveness
            {"book_number": 40, "chapter": 6, "verse": 9, "text": '"This, then, is how you should pray: Our Father in heaven, hallowed be your name,'},
            {"book_number": 40, "chapter": 6, "verse": 10, "text": "your kingdom come, your will be done, on earth as it is in heaven."},
            {"book_number": 40, "chapter": 6, "verse": 11, "text": "Give us today our daily bread."},
            {"book_number": 40, "chapter": 6, "verse": 12, "text": "And forgive us our debts, as we also have forgiven our debtors."},
            {"book_number": 40, "chapter": 6, "verse": 13, "text": "And lead us not into temptation, but deliver us from the evil one."},
            {"book_number": 40, "chapter": 6, "verse": 14, "text": "For if you forgive other people when they sin against you, your heavenly Father will also forgive you."},
            {"book_number": 40, "chapter": 6, "verse": 15, "text": "But if you do not forgive others their sins, your Father will not forgive your sins."},
            # 1 Corinthians 13 - Love chapter
            {"book_number": 46, "chapter": 13, "verse": 1, "text": "If I speak in the tongues of men or of angels, but do not have love, I am only a resounding gong or a clanging cymbal."},
            {"book_number": 46, "chapter": 13, "verse": 2, "text": "If I have the gift of prophecy and can fathom all mysteries and all knowledge, and if I have a faith that can move mountains, but do not have love, I am nothing."},
            {"book_number": 46, "chapter": 13, "verse": 3, "text": "If I give all I possess to the poor and give over my body to hardship that I may boast, but do not have love, I gain nothing."},
            {"book_number": 46, "chapter": 13, "verse": 4, "text": "Love is patient, love is kind. It does not envy, it does not boast, it is not proud."},
            {"book_number": 46, "chapter": 13, "verse": 5, "text": "It does not dishonor others, it is not self-seeking, it is not easily angered, it keeps no record of wrongs."},
            {"book_number": 46, "chapter": 13, "verse": 6, "text": "Love does not delight in evil but rejoices with the truth."},
            {"book_number": 46, "chapter": 13, "verse": 7, "text": "It always protects, always trusts, always hopes, always perseveres."},
            {"book_number": 46, "chapter": 13, "verse": 13, "text": "And now these three remain: faith, hope and love. But the greatest of these is love."},
            # Romans 8 - No condemnation
            {"book_number": 45, "chapter": 8, "verse": 1, "text": "Therefore, there is now no condemnation for those who are in Christ Jesus,"},
            {"book_number": 45, "chapter": 8, "verse": 28, "text": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose."},
            {"book_number": 45, "chapter": 8, "verse": 38, "text": "For I am convinced that neither death nor life, neither angels nor demons, neither the present nor the future, nor any powers,"},
            {"book_number": 45, "chapter": 8, "verse": 39, "text": "neither height nor depth, nor anything else in all creation, will be able to separate us from the love of God that is in Christ Jesus our Lord."},
            # Genesis 1
            {"book_number": 1, "chapter": 1, "verse": 1, "text": "In the beginning God created the heavens and the earth."},
            {"book_number": 1, "chapter": 1, "verse": 2, "text": "Now the earth was formless and empty, darkness was over the surface of the deep, and the Spirit of God was hovering over the waters."},
            {"book_number": 1, "chapter": 1, "verse": 3, "text": 'And God said, "Let there be light," and there was light.'},
            # Psalms 23
            {"book_number": 19, "chapter": 23, "verse": 1, "text": "The Lord is my shepherd, I lack nothing."},
            {"book_number": 19, "chapter": 23, "verse": 2, "text": "He makes me lie down in green pastures, he leads me beside quiet waters,"},
            {"book_number": 19, "chapter": 23, "verse": 3, "text": "he refreshes my soul. He guides me along the right paths for his name's sake."},
            {"book_number": 19, "chapter": 23, "verse": 4, "text": "Even though I walk through the darkest valley, I will fear no evil, for you are with me; your rod and your staff, they comfort me."},
        ],
        "RKV": [
            {"book_number": 43, "chapter": 3, "verse": 1, "text": "그런데 바리새인 중에 니고데모라 하는 사람이 있으니 유대인의 지도자라"},
            {"book_number": 43, "chapter": 3, "verse": 2, "text": "그가 밤에 예수께 와서 이르되 랍비여 우리가 당신은 하나님께로부터 오신 선생인 줄 아나이다 하나님이 함께 하시지 아니하시면 당신이 행하시는 이 표적을 아무도 할 수 없음이니이다"},
            {"book_number": 43, "chapter": 3, "verse": 3, "text": "예수께서 대답하여 이르시되 진실로 진실로 네게 이르노니 사람이 거듭나지 아니하면 하나님의 나라를 볼 수 없느니라"},
            {"book_number": 43, "chapter": 3, "verse": 14, "text": "모세가 광야에서 뱀을 든 것 같이 인자도 들려야 하리니"},
            {"book_number": 43, "chapter": 3, "verse": 15, "text": "이는 그를 믿는 자마다 영생을 얻게 하려 하심이니라"},
            {"book_number": 43, "chapter": 3, "verse": 16, "text": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라"},
            {"book_number": 43, "chapter": 3, "verse": 17, "text": "하나님이 그 아들을 세상에 보내신 것은 세상을 심판하려 하심이 아니요 그로 말미암아 세상이 구원을 받게 하려 하심이라"},
            # Matthew 6 - 주기도문
            {"book_number": 40, "chapter": 6, "verse": 9, "text": "그러므로 너희는 이렇게 기도하라 하늘에 계신 우리 아버지여 이름이 거룩히 여김을 받으시오며"},
            {"book_number": 40, "chapter": 6, "verse": 10, "text": "나라가 임하시오며 뜻이 하늘에서 이루어진 것 같이 땅에서도 이루어지이다"},
            {"book_number": 40, "chapter": 6, "verse": 11, "text": "오늘 우리에게 일용할 양식을 주시옵고"},
            {"book_number": 40, "chapter": 6, "verse": 12, "text": "우리가 우리에게 죄 지은 자를 사하여 준 것 같이 우리 죄를 사하여 주시옵고"},
            {"book_number": 40, "chapter": 6, "verse": 13, "text": "우리를 시험에 들게 하지 마시옵고 다만 악에서 구하시옵소서"},
            {"book_number": 40, "chapter": 6, "verse": 14, "text": "너희가 사람의 잘못을 용서하면 너희 하늘 아버지께서도 너희 잘못을 용서하시려니와"},
            {"book_number": 40, "chapter": 6, "verse": 15, "text": "너희가 사람의 잘못을 용서하지 아니하면 너희 아버지께서도 너희 잘못을 용서하지 아니하시리라"},
            # 고린도전서 13 - 사랑장
            {"book_number": 46, "chapter": 13, "verse": 1, "text": "내가 사람의 방언과 천사의 말을 할지라도 사랑이 없으면 소리 나는 구리와 울리는 꽹과리가 되고"},
            {"book_number": 46, "chapter": 13, "verse": 2, "text": "내가 예언하는 능력이 있어 모든 비밀과 모든 지식을 알고 또 산을 옮길 만한 모든 믿음이 있을지라도 사랑이 없으면 내가 아무 것도 아니요"},
            {"book_number": 46, "chapter": 13, "verse": 3, "text": "내가 내게 있는 모든 것으로 구제하고 또 내 몸을 불사르게 내줄지라도 사랑이 없으면 내게 아무 유익이 없느니라"},
            {"book_number": 46, "chapter": 13, "verse": 4, "text": "사랑은 오래 참고 사랑은 온유하며 시기하지 아니하며 사랑은 자랑하지 아니하며 교만하지 아니하며"},
            {"book_number": 46, "chapter": 13, "verse": 5, "text": "무례히 행하지 아니하며 자기의 유익을 구하지 아니하며 성내지 아니하며 악한 것을 생각하지 아니하며"},
            {"book_number": 46, "chapter": 13, "verse": 6, "text": "불의를 기뻐하지 아니하며 진리와 함께 기뻐하고"},
            {"book_number": 46, "chapter": 13, "verse": 7, "text": "모든 것을 참으며 모든 것을 믿으며 모든 것을 바라며 모든 것을 견디느니라"},
            {"book_number": 46, "chapter": 13, "verse": 13, "text": "그런즉 믿음, 소망, 사랑, 이 세 가지는 항상 있을 것인데 그 중의 제일은 사랑이라"},
            # 로마서 8
            {"book_number": 45, "chapter": 8, "verse": 1, "text": "그러므로 이제 그리스도 예수 안에 있는 자에게는 결코 정죄함이 없나니"},
            {"book_number": 45, "chapter": 8, "verse": 28, "text": "우리가 알거니와 하나님을 사랑하는 자 곧 그의 뜻대로 부르심을 입은 자들에게는 모든 것이 합력하여 선을 이루느니라"},
            {"book_number": 45, "chapter": 8, "verse": 38, "text": "내가 확신하노니 사망이나 생명이나 천사들이나 권세자들이나 현재 일이나 장래 일이나 능력이나"},
            {"book_number": 45, "chapter": 8, "verse": 39, "text": "높음이나 깊음이나 다른 어떤 피조물이라도 우리를 우리 주 그리스도 예수 안에 있는 하나님의 사랑에서 끊을 수 없으리라"},
            # 창세기 1
            {"book_number": 1, "chapter": 1, "verse": 1, "text": "태초에 하나님이 천지를 창조하시니라"},
            {"book_number": 1, "chapter": 1, "verse": 2, "text": "땅이 혼돈하고 공허하며 흑암이 깊음 위에 있고 하나님의 영은 수면 위에 운행하시니라"},
            {"book_number": 1, "chapter": 1, "verse": 3, "text": "하나님이 이르시되 빛이 있으라 하시니 빛이 있었고"},
            # 시편 23
            {"book_number": 19, "chapter": 23, "verse": 1, "text": "여호와는 나의 목자시니 내게 부족함이 없으리로다"},
            {"book_number": 19, "chapter": 23, "verse": 2, "text": "그가 나를 푸른 풀밭에 누이시며 쉴 만한 물 가로 인도하시는도다"},
            {"book_number": 19, "chapter": 23, "verse": 3, "text": "내 영혼을 소생시키시고 자기 이름을 위하여 의의 길로 인도하시는도다"},
            {"book_number": 19, "chapter": 23, "verse": 4, "text": "내가 사망의 음침한 골짜기로 다닐지라도 해를 두려워하지 않을 것은 주께서 나와 함께 하심이라 주의 지팡이와 막대기가 나를 안위하시나이다"},
        ],
    }

    return sample_verses.get(translation_abbrev, [])


def ingest_translation(
    db: Session,
    translation: Translation,
    books_map: dict[int, Book],
    verses_data: Optional[list[dict]] = None,
) -> int:
    """Ingest a complete Bible translation.

    Args:
        db: Database session
        translation: Translation object
        books_map: Mapping of book_number -> Book object
        verses_data: Optional list of verse data. If not provided,
                     will try to load from online source.

    Returns:
        Number of verses inserted
    """
    if verses_data is None:
        verses_data = load_bible_data(translation.abbreviation)

    if not verses_data:
        print(f"No verse data available for {translation.abbreviation}")
        return 0

    count = insert_verses_batch(db, verses_data, translation, books_map)
    print(f"Inserted {count} verses for {translation.abbreviation}")
    return count


def run_ingestion(
    translations_to_load: Optional[list[str]] = None,
    reset_database: bool = True,
):
    """Run the complete data ingestion process.

    Args:
        translations_to_load: List of translation abbreviations to load.
                             If None, loads all available public domain translations.
        reset_database: If True, clears all verses before ingestion (default: True)

    Note:
        For original language ingestion (Greek, Hebrew, Aramaic), use
        scripts/original_ingestion.py instead.
    """
    if translations_to_load is None:
        # Default: All free translations from Bolls.life + GetBible APIs
        # ✅ Bolls.life API is back online (verified 2026-01-13)
        translations_to_load = [
            # English translations (Bolls.life - free, no API key required)
            "NIV",      # New International Version (most popular)
            "ESV",      # English Standard Version (literal)
            "NASB",     # New American Standard Bible (very literal)
            "NKJV",     # New King James Version (updated KJV)
            "NLT",      # New Living Translation (readable)

            # English translations (GetBible - public domain, reliable)
            "KJV",      # King James Version (traditional)
            "WEB",      # World English Bible (modern public domain)

            # Korean translations (Bolls.life - free)
            "KRV",      # 개역한글 (Korean Revised Version, copyright expired 2011)
            "RNKSV",    # 새번역 (New Korean Revised Standard Version)

            # Korean translation (GetBible - public domain)
            "RKV",      # 개역성경 (Korean Revised Version)

            # ⚠️  개역개정 (educational use only) - Requires bible2_1.sql or bible2 1.sql file
            "NKRV",     # 개역개정 (New Korean Revised Version, 1998)
        ]

    db = SessionLocal()

    try:
        print("Initializing database...")
        init_db()

        # Clear existing verses if requested
        if reset_database:
            print("\n⚠️  Resetting database - deleting all existing verses...")
            verse_count = db.query(Verse).count()
            if verse_count > 0:
                db.query(Verse).delete()
                db.commit()
                print(f"Deleted {verse_count} existing verses")

        print("Initializing translations...")
        translations_map = init_translations(db)

        print("Initializing books...")
        books_map = init_books(db)

        print("Ingesting verses...")
        total_verses = 0

        for abbrev in translations_to_load:
            translation = translations_map.get(abbrev)
            if translation:
                count = ingest_translation(db, translation, books_map)
                total_verses += count
            else:
                print(f"Translation {abbrev} not found")

        print(f"\n🎉 Ingestion complete! Total verses: {total_verses}")

    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()
