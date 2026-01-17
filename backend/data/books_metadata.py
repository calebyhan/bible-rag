"""Bible books metadata - 66 books with names, testament, genre, and chapter counts."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BookMetadata:
    """Metadata for a Bible book."""

    book_number: int
    name: str
    name_korean: str
    abbreviation: str
    testament: str  # 'OT' or 'NT'
    genre: str
    total_chapters: int
    name_original: Optional[str] = None


# Complete list of 66 Bible books
BOOKS_METADATA: list[BookMetadata] = [
    # Old Testament - Law (Torah/Pentateuch)
    BookMetadata(1, "Genesis", "창세기", "Gen", "OT", "law", 50, "בְּרֵאשִׁית"),
    BookMetadata(2, "Exodus", "출애굽기", "Exod", "OT", "law", 40, "שְׁמוֹת"),
    BookMetadata(3, "Leviticus", "레위기", "Lev", "OT", "law", 27, "וַיִּקְרָא"),
    BookMetadata(4, "Numbers", "민수기", "Num", "OT", "law", 36, "בְּמִדְבַּר"),
    BookMetadata(5, "Deuteronomy", "신명기", "Deut", "OT", "law", 34, "דְּבָרִים"),
    # Old Testament - History
    BookMetadata(6, "Joshua", "여호수아", "Josh", "OT", "history", 24, "יְהוֹשֻׁעַ"),
    BookMetadata(7, "Judges", "사사기", "Judg", "OT", "history", 21, "שׁוֹפְטִים"),
    BookMetadata(8, "Ruth", "룻기", "Ruth", "OT", "history", 4, "רוּת"),
    BookMetadata(9, "1 Samuel", "사무엘상", "1Sam", "OT", "history", 31, "שְׁמוּאֵל א"),
    BookMetadata(10, "2 Samuel", "사무엘하", "2Sam", "OT", "history", 24, "שְׁמוּאֵל ב"),
    BookMetadata(11, "1 Kings", "열왕기상", "1Kgs", "OT", "history", 22, "מְלָכִים א"),
    BookMetadata(12, "2 Kings", "열왕기하", "2Kgs", "OT", "history", 25, "מְלָכִים ב"),
    BookMetadata(13, "1 Chronicles", "역대상", "1Chr", "OT", "history", 29, "דִּבְרֵי הַיָּמִים א"),
    BookMetadata(14, "2 Chronicles", "역대하", "2Chr", "OT", "history", 36, "דִּבְרֵי הַיָּמִים ב"),
    BookMetadata(15, "Ezra", "에스라", "Ezra", "OT", "history", 10, "עֶזְרָא"),
    BookMetadata(16, "Nehemiah", "느헤미야", "Neh", "OT", "history", 13, "נְחֶמְיָה"),
    BookMetadata(17, "Esther", "에스더", "Esth", "OT", "history", 10, "אֶסְתֵּר"),
    # Old Testament - Poetry/Wisdom
    BookMetadata(18, "Job", "욥기", "Job", "OT", "wisdom", 42, "אִיּוֹב"),
    BookMetadata(19, "Psalms", "시편", "Ps", "OT", "poetry", 150, "תְּהִלִּים"),
    BookMetadata(20, "Proverbs", "잠언", "Prov", "OT", "wisdom", 31, "מִשְׁלֵי"),
    BookMetadata(21, "Ecclesiastes", "전도서", "Eccl", "OT", "wisdom", 12, "קֹהֶלֶת"),
    BookMetadata(22, "Song of Solomon", "아가", "Song", "OT", "poetry", 8, "שִׁיר הַשִּׁירִים"),
    # Old Testament - Major Prophets
    BookMetadata(23, "Isaiah", "이사야", "Isa", "OT", "prophecy", 66, "יְשַׁעְיָהוּ"),
    BookMetadata(24, "Jeremiah", "예레미야", "Jer", "OT", "prophecy", 52, "יִרְמְיָהוּ"),
    BookMetadata(25, "Lamentations", "예레미야애가", "Lam", "OT", "poetry", 5, "אֵיכָה"),
    BookMetadata(26, "Ezekiel", "에스겔", "Ezek", "OT", "prophecy", 48, "יְחֶזְקֵאל"),
    BookMetadata(27, "Daniel", "다니엘", "Dan", "OT", "prophecy", 12, "דָּנִיֵּאל"),
    # Old Testament - Minor Prophets
    BookMetadata(28, "Hosea", "호세아", "Hos", "OT", "prophecy", 14, "הוֹשֵׁעַ"),
    BookMetadata(29, "Joel", "요엘", "Joel", "OT", "prophecy", 3, "יוֹאֵל"),
    BookMetadata(30, "Amos", "아모스", "Amos", "OT", "prophecy", 9, "עָמוֹס"),
    BookMetadata(31, "Obadiah", "오바댜", "Obad", "OT", "prophecy", 1, "עֹבַדְיָה"),
    BookMetadata(32, "Jonah", "요나", "Jonah", "OT", "prophecy", 4, "יוֹנָה"),
    BookMetadata(33, "Micah", "미가", "Mic", "OT", "prophecy", 7, "מִיכָה"),
    BookMetadata(34, "Nahum", "나훔", "Nah", "OT", "prophecy", 3, "נַחוּם"),
    BookMetadata(35, "Habakkuk", "하박국", "Hab", "OT", "prophecy", 3, "חֲבַקּוּק"),
    BookMetadata(36, "Zephaniah", "스바냐", "Zeph", "OT", "prophecy", 3, "צְפַנְיָה"),
    BookMetadata(37, "Haggai", "학개", "Hag", "OT", "prophecy", 2, "חַגַּי"),
    BookMetadata(38, "Zechariah", "스가랴", "Zech", "OT", "prophecy", 14, "זְכַרְיָה"),
    BookMetadata(39, "Malachi", "말라기", "Mal", "OT", "prophecy", 4, "מַלְאָכִי"),
    # New Testament - Gospels
    BookMetadata(40, "Matthew", "마태복음", "Matt", "NT", "gospel", 28, "Κατὰ Ματθαῖον"),
    BookMetadata(41, "Mark", "마가복음", "Mark", "NT", "gospel", 16, "Κατὰ Μᾶρκον"),
    BookMetadata(42, "Luke", "누가복음", "Luke", "NT", "gospel", 24, "Κατὰ Λουκᾶν"),
    BookMetadata(43, "John", "요한복음", "John", "NT", "gospel", 21, "Κατὰ Ἰωάννην"),
    # New Testament - History
    BookMetadata(44, "Acts", "사도행전", "Acts", "NT", "history", 28, "Πράξεις Ἀποστόλων"),
    # New Testament - Pauline Epistles
    BookMetadata(45, "Romans", "로마서", "Rom", "NT", "epistle", 16, "Πρὸς Ῥωμαίους"),
    BookMetadata(46, "1 Corinthians", "고린도전서", "1Cor", "NT", "epistle", 16, "Πρὸς Κορινθίους Αʹ"),
    BookMetadata(47, "2 Corinthians", "고린도후서", "2Cor", "NT", "epistle", 13, "Πρὸς Κορινθίους Βʹ"),
    BookMetadata(48, "Galatians", "갈라디아서", "Gal", "NT", "epistle", 6, "Πρὸς Γαλάτας"),
    BookMetadata(49, "Ephesians", "에베소서", "Eph", "NT", "epistle", 6, "Πρὸς Ἐφεσίους"),
    BookMetadata(50, "Philippians", "빌립보서", "Phil", "NT", "epistle", 4, "Πρὸς Φιλιππησίους"),
    BookMetadata(51, "Colossians", "골로새서", "Col", "NT", "epistle", 4, "Πρὸς Κολοσσαεῖς"),
    BookMetadata(52, "1 Thessalonians", "데살로니가전서", "1Thess", "NT", "epistle", 5, "Πρὸς Θεσσαλονικεῖς Αʹ"),
    BookMetadata(53, "2 Thessalonians", "데살로니가후서", "2Thess", "NT", "epistle", 3, "Πρὸς Θεσσαλονικεῖς Βʹ"),
    BookMetadata(54, "1 Timothy", "디모데전서", "1Tim", "NT", "epistle", 6, "Πρὸς Τιμόθεον Αʹ"),
    BookMetadata(55, "2 Timothy", "디모데후서", "2Tim", "NT", "epistle", 4, "Πρὸς Τιμόθεον Βʹ"),
    BookMetadata(56, "Titus", "디도서", "Titus", "NT", "epistle", 3, "Πρὸς Τίτον"),
    BookMetadata(57, "Philemon", "빌레몬서", "Phlm", "NT", "epistle", 1, "Πρὸς Φιλήμονα"),
    # New Testament - General Epistles
    BookMetadata(58, "Hebrews", "히브리서", "Heb", "NT", "epistle", 13, "Πρὸς Ἑβραίους"),
    BookMetadata(59, "James", "야고보서", "Jas", "NT", "epistle", 5, "Ἰακώβου"),
    BookMetadata(60, "1 Peter", "베드로전서", "1Pet", "NT", "epistle", 5, "Πέτρου Αʹ"),
    BookMetadata(61, "2 Peter", "베드로후서", "2Pet", "NT", "epistle", 3, "Πέτρου Βʹ"),
    BookMetadata(62, "1 John", "요한일서", "1John", "NT", "epistle", 5, "Ἰωάννου Αʹ"),
    BookMetadata(63, "2 John", "요한이서", "2John", "NT", "epistle", 1, "Ἰωάννου Βʹ"),
    BookMetadata(64, "3 John", "요한삼서", "3John", "NT", "epistle", 1, "Ἰωάννου Γʹ"),
    BookMetadata(65, "Jude", "유다서", "Jude", "NT", "epistle", 1, "Ἰούδα"),
    # New Testament - Prophecy
    BookMetadata(66, "Revelation", "요한계시록", "Rev", "NT", "prophecy", 22, "Ἀποκάλυψις Ἰωάννου"),
]


def get_book_by_number(book_number: int) -> Optional[BookMetadata]:
    """Get book metadata by book number (1-66)."""
    for book in BOOKS_METADATA:
        if book.book_number == book_number:
            return book
    return None


def get_book_by_name(name: str) -> Optional[BookMetadata]:
    """Get book metadata by name (English or Korean)."""
    name_lower = name.lower()
    for book in BOOKS_METADATA:
        if (
            book.name.lower() == name_lower
            or book.name_korean == name
            or book.abbreviation.lower() == name_lower
        ):
            return book
    return None


def get_books_by_testament(testament: str) -> list[BookMetadata]:
    """Get all books in a testament ('OT' or 'NT')."""
    return [book for book in BOOKS_METADATA if book.testament == testament]


def get_books_by_genre(genre: str) -> list[BookMetadata]:
    """Get all books of a specific genre."""
    return [book for book in BOOKS_METADATA if book.genre == genre]


# Translation metadata
TRANSLATIONS = [
    {
        "name": "New International Version",
        "abbreviation": "NIV",
        "language_code": "en",
        "description": "Contemporary English translation known for readability",
        "is_original_language": False,
    },
    {
        "name": "English Standard Version",
        "abbreviation": "ESV",
        "language_code": "en",
        "description": "Essentially literal English translation",
        "is_original_language": False,
    },
    {
        "name": "New American Standard Bible",
        "abbreviation": "NASB",
        "language_code": "en",
        "description": "Literal English translation known for accuracy",
        "is_original_language": False,
    },
    {
        "name": "King James Version",
        "abbreviation": "KJV",
        "language_code": "en",
        "description": "Classic English translation from 1611",
        "is_original_language": False,
    },
    {
        "name": "New King James Version",
        "abbreviation": "NKJV",
        "language_code": "en",
        "description": "Modern English update of KJV",
        "is_original_language": False,
    },
    {
        "name": "New Living Translation",
        "abbreviation": "NLT",
        "language_code": "en",
        "description": "Dynamic equivalence English translation for readability",
        "is_original_language": False,
    },
    {
        "name": "World English Bible",
        "abbreviation": "WEB",
        "language_code": "en",
        "description": "Public domain modern English translation",
        "is_original_language": False,
    },
    {
        "name": "개역개정",
        "abbreviation": "NKRV",
        "language_code": "ko",
        "description": "New Korean Revised Version (1998) - most commonly used Korean translation",
        "is_original_language": False,
    },
    {
        "name": "개역한글",
        "abbreviation": "KRV",
        "language_code": "ko",
        "description": "Korean Revised Version (1961) - traditional, public domain since 2011",
        "is_original_language": False,
    },
    {
        "name": "개역성경",
        "abbreviation": "RKV",
        "language_code": "ko",
        "description": "Revised Korean Bible - older version",
        "is_original_language": False,
    },
    {
        "name": "새번역",
        "abbreviation": "RNKSV",
        "language_code": "ko",
        "description": "New Korean Revised Standard Version - modern language",
        "is_original_language": False,
    },
    {
        "name": "공동번역",
        "abbreviation": "KCBS",
        "language_code": "ko",
        "description": "Korean Common Bible - ecumenical translation",
        "is_original_language": False,
    },
    {
        "name": "SBL Greek New Testament",
        "abbreviation": "SBLGNT",
        "language_code": "gr",
        "description": "Society of Biblical Literature Greek New Testament",
        "is_original_language": True,
    },
    {
        "name": "Greek New Testament (OpenGNT)",
        "abbreviation": "GNT",
        "language_code": "gr",
        "description": "Open Greek New Testament - NA28 equivalent with Strong's numbers",
        "is_original_language": True,
    },
    {
        "name": "Westminster Leningrad Codex",
        "abbreviation": "WLC",
        "language_code": "he",
        "description": "Hebrew Old Testament based on Leningrad Codex",
        "is_original_language": True,
    },
    {
        "name": "Hebrew Old Testament (WLC)",
        "abbreviation": "HEB",
        "language_code": "he",
        "description": "Hebrew Old Testament - Westminster Leningrad Codex",
        "is_original_language": True,
    },
    {
        "name": "Aramaic Portions (WLC)",
        "abbreviation": "ARA",
        "language_code": "arc",
        "description": "Aramaic portions of Daniel and Ezra from WLC",
        "is_original_language": True,
    },
]
