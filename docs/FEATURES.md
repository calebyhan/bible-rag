# Bible RAG - Features Documentation

Comprehensive guide to all features of the Bible RAG system with examples and usage tips.

## Table of Contents

- [Semantic Search](#semantic-search)
- [Multi-Translation Support](#multi-translation-support)
- [Parallel Translation View](#parallel-translation-view)
- [Original Language Integration](#original-language-integration)
- [Korean-Specific Features](#korean-specific-features)
- [Cross-Reference Discovery](#cross-reference-discovery)
- [Theological Term Glossary](#theological-term-glossary)
- [Smart Query Understanding](#smart-query-understanding)
- [Browse & Navigation](#browse--navigation)
- [Advanced Search Filters](#advanced-search-filters)

---

## Semantic Search

### How It Works

Semantic search understands the **meaning** of your query, not just keywords. Instead of exact word matching, the system uses AI embeddings to find verses that are conceptually similar to what you're looking for.

**Traditional keyword search:**
- Query: "love" → Only finds verses with the exact word "love"
- Misses: verses about "affection", "devotion", "compassion"

**Semantic search:**
- Query: "love" → Finds verses about love, affection, compassion, charity, caring
- Understands context and related concepts

### Example Queries

#### English Queries

**1. Concept-Based Search**
```
Query: "What does Jesus say about forgiveness?"
Results: Matthew 6:14-15, Luke 6:37, Mark 11:25, Matthew 18:21-22
```

**2. Thematic Search**
```
Query: "faith and works"
Results: James 2:14-26, Ephesians 2:8-10, Galatians 5:6
```

**3. Character Search**
```
Query: "Paul's letters about grace"
Results: Romans 3:23-24, Ephesians 2:4-9, Titus 2:11-14
```

**4. Situational Search**
```
Query: "comfort during difficult times"
Results: Psalm 23, Matthew 11:28-30, 2 Corinthians 1:3-4
```

#### Korean Queries (한국어 검색)

**1. 개념 기반 검색**
```
Query: "사랑에 대한 예수님의 가르침"
Results: 요한복음 13:34-35, 마태복음 22:37-40, 요한일서 4:7-12
```

**2. 주제 검색**
```
Query: "믿음과 행위"
Results: 야고보서 2:14-26, 에베소서 2:8-10
```

**3. 상황별 검색**
```
Query: "어려울 때 위로받는 말씀"
Results: 시편 23편, 마태복음 11:28-30, 고린도후서 1:3-4
```

#### Mixed Language Queries (코드 스위칭)

```
Query: "요한복음에서 love에 대한 구절"
Results: John 13:34-35 (요한복음 13:34-35), John 15:12-13
```

```
Query: "What did 바울 say about grace?"
Results: Romans 3:23-24 (로마서 3:23-24), Ephesians 2:8-9
```

### Tips for Best Results

1. **Be specific about what you're looking for:**
   - ❌ "love"
   - ✅ "God's unconditional love for humanity"

2. **Ask questions naturally:**
   - ✅ "What does the Bible say about worry?"
   - ✅ "How should Christians treat their enemies?"

3. **Use context:**
   - ✅ "Jesus' teaching about prayer in the Sermon on the Mount"
   - ✅ "Paul's advice to Timothy about leadership"

4. **Combine concepts:**
   - ✅ "faith, hope, and love"
   - ✅ "wisdom and understanding"

---

## Multi-Translation Support

### Available Translations

#### English Translations

| Abbreviation | Name | Style | Year |
|--------------|------|-------|------|
| **NIV** | New International Version | Contemporary, balanced | 2011 |
| **ESV** | English Standard Version | Literal, literary | 2001 |
| **NASB** | New American Standard Bible | Very literal | 1995 |

#### Korean Translations (한국어 번역)

| Abbreviation | Name | Style | Year |
|--------------|------|-------|------|
| **개역개정** | Revised Korean Version | Standard Korean Protestant | 1998 |
| **개역한글** | Korean Revised Version | Traditional Korean | 1961 |
| **새번역** | New Korean Revised Version | Contemporary Korean | 2004 |
| **공동번역** | Common Translation | Ecumenical (Catholic/Protestant) | 1977 |

#### Original Languages

| Abbreviation | Name | Testament |
|--------------|------|-----------|
| **SBLGNT** | SBL Greek New Testament | NT |
| **WLC** | Westminster Leningrad Codex | OT |

### How to Switch Translations

**In Search:**
```json
{
  "query": "John 3:16",
  "translations": ["NIV", "ESV", "개역개정"]
}
```

**In UI:**
- Click translation selector
- Check desired translations
- Search results show all selected translations

### Translation Comparison

Different translations can provide different perspectives:

**Example: Philippians 4:13**

- **NIV:** "I can do all this through him who gives me strength."
- **ESV:** "I can do all things through him who strengthens me."
- **NASB:** "I can do all things through Him who strengthens me."
- **개역개정:** "내게 능력 주시는 자 안에서 내가 모든 것을 할 수 있느니라"
- **새번역:** "나를 능력 있게 하시는 분 안에서, 나는 모든 것을 할 수 있습니다"

---

## Parallel Translation View

### Side-by-Side Comparison

View the same verse across multiple translations simultaneously.

**Example: John 3:16**

```
┌─────────────────────────────────────────────────────────────────┐
│ John 3:16 (요한복음 3:16)                                         │
├─────────────────────────────────────────────────────────────────┤
│ [EN-NIV]                                                         │
│ For God so loved the world that he gave his one and only Son,   │
│ that whoever believes in him shall not perish but have eternal  │
│ life.                                                            │
├─────────────────────────────────────────────────────────────────┤
│ [KO-개역개정]                                                     │
│ 하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 그를      │
│ 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라              │
├─────────────────────────────────────────────────────────────────┤
│ [GR-Original]                                                    │
│ οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον, ὥστε τὸν υἱὸν τὸν       │
│ μονογενῆ ἔδωκεν                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Highlighting Differences

The system can highlight key differences between translations:

**Example: Matthew 5:3**

- **NIV:** "Blessed are the **poor in spirit**"
- **ESV:** "Blessed are the **poor in spirit**"
- **개역개정:** "**심령이 가난한 자**는 복이 있나니"
- **새번역:** "**마음이 가난한 사람**은 복이 있다"

Different words for "poor in spirit": 심령 (spirit/soul) vs 마음 (heart/mind)

---

## Original Language Integration

### Greek (New Testament)

#### Strong's Concordance Numbers

Every Greek word is tagged with a Strong's number (G1-G5624).

**Example: ἀγαπάω (agapaō) - "to love"**

```
Strong's: G25
Transliteration: agapaō
Pronunciation: ag-ap-ah'-o
Morphology: V-AAI-3S (Verb, Aorist, Active, Indicative, 3rd person, Singular)
Definition: to love, to have affection for, to welcome, to be fond of
Usage: Of divine and human love, expressing affection and benevolence
```

#### Morphological Parsing

Understanding Greek grammar:

| Code | Meaning | Example |
|------|---------|---------|
| **V** | Verb | ἀγαπάω (love) |
| **N** | Noun | λόγος (word) |
| **A** | Adjective | ἀγαθός (good) |
| **AAI** | Aorist, Active, Indicative | Past tense, active voice |
| **3S** | 3rd person, Singular | he/she/it |

#### Word Study Example

**John 21:15-17 - "Love" in Greek**

Three different questions about love:
1. "Simon... do you **love** (ἀγαπάω - agapaō) me?" → Divine love
2. "Simon... do you **love** (ἀγαπάω - agapaō) me?" → Divine love
3. "Simon... do you **love** (φιλέω - phileō) me?" → Friendship love

Peter's responses:
1. "Yes, Lord; you know that I **love** (φιλέω - phileō) you" → Friendship love
2. "Yes, Lord; you know that I **love** (φιλέω - phileō) you" → Friendship love
3. "Lord... you know that I **love** (φιλέω - phileō) you" → Friendship love

### Hebrew (Old Testament)

#### Strong's Numbers (H1-H8674)

**Example: אָהַב (ahav) - "to love"**

```
Strong's: H157
Transliteration: 'ahab
Pronunciation: aw-hab'
Root: אהב
Definition: to love, to have affection
Usage: Human love, divine love, love of objects/activities
```

#### Vowel Pointing (Niqqud)

Hebrew text includes vowel marks:

```
Original (with vowels): בְּרֵאשִׁית
Without vowels: בראשית
Transliteration: berēshiyth
Meaning: "In the beginning" (Genesis 1:1)
```

---

## Korean-Specific Features

### Hanja (한자) Display

Show Chinese characters for theological terms to deepen understanding.

**Toggle On:**
```
속죄 (贖罪) - Atonement
구원 (救援) - Salvation
은혜 (恩惠) - Grace
믿음 (信) - Faith
소망 (所望) - Hope
사랑 (愛) - Love
```

**Why Hanja Matters:**
- Many Korean theological terms are Sino-Korean (한자어)
- Seeing Hanja clarifies meaning (救 = rescue, 援 = help)
- Helps understand relationship between concepts

### Romanization (로마자)

Display Korean text in Roman letters for pronunciation.

**Example:**
```
Original: 하나님이 세상을 이처럼 사랑하사
Romanization: Hananim-i sesang-eul icheoreom saranghasa
Translation: God so loved the world
```

**Use Cases:**
- Korean learners
- Non-Korean speakers studying Korean Bible
- Pronunciation practice

### Typography Optimization

Korean text has special formatting:

1. **Line Height: 1.8-2.0** (vs 1.5 for English)
   - Korean characters are denser visually
   - Need more vertical spacing for readability

2. **Font: Noto Sans KR, 나눔고딕**
   - Optimized for screen readability
   - Proper weight distribution

3. **Font Size: 16px minimum** (vs 14px for English)
   - Korean has more visual complexity per character

### Honorific Language Handling

Korean has multiple speech levels. The system uses appropriate honorifics when referring to God and biblical figures.

**Example:**
- 하나님**께서** (honorific subject marker)
- 말씀**하시다** (honorific verb form)
- **드리다** (humble form of "give")

---

## Cross-Reference Discovery

### Types of Cross-References

#### 1. Parallel Passages

Same event in different gospels:

**Example: Feeding of the 5000**
- Matthew 14:13-21
- Mark 6:30-44
- Luke 9:10-17
- John 6:1-15

#### 2. Prophecy-Fulfillment

Old Testament prophecies fulfilled in New Testament:

**Example: Virgin Birth**
- **Prophecy:** Isaiah 7:14 - "The virgin will conceive and give birth to a son"
- **Fulfillment:** Matthew 1:22-23 - "All this took place to fulfill what the Lord had said"

#### 3. Quotations

Direct quotes from other biblical books:

**Example: Greatest Commandment**
- **Original:** Deuteronomy 6:5 - "Love the LORD your God with all your heart"
- **Quoted:** Matthew 22:37, Mark 12:30, Luke 10:27

#### 4. Thematic Links

Verses related by concept:

**Example: Faith**
- Hebrews 11:1 - "Faith is confidence in what we hope for"
- Romans 10:17 - "Faith comes from hearing the message"
- James 2:17 - "Faith by itself, if it is not accompanied by action, is dead"

### How to Use Cross-References

1. **Click on verse** → View details
2. **See "Related Verses" section** → List of cross-references
3. **Click reference chip** → Navigate to related verse
4. **Compare contexts** → Understand deeper connections

---

## Theological Term Glossary

### Multilingual Term Mapping

Korean → English → Original Language

```
속죄 (sokjoe) = Atonement = כָּפַר (kaphar, H3722)
구원 (guwon) = Salvation = σωτηρία (soteria, G4991)
은혜 (eunhye) = Grace = χάρις (charis, G5485)
믿음 (mideum) = Faith = πίστις (pistis, G4102)
의 (ui) = Righteousness = δικαιοσύνη (dikaiosunē, G1343)
성령 (seongryeong) = Holy Spirit = πνεῦμα ἅγιον (pneuma hagion)
```

### How to Access

1. **Hover over theological term** in verse text
2. **See popup** with:
   - Korean term + Hanja
   - English equivalent
   - Original Greek/Hebrew
   - Strong's number
   - Brief definition

**Example:**
```
┌─────────────────────────────────────┐
│ 은혜 (恩惠)                          │
│ ─────────────────────────────────   │
│ English: Grace                      │
│ Greek: χάρις (charis, G5485)        │
│ Definition: Unmerited favor,        │
│ divine blessing                     │
└─────────────────────────────────────┘
```

---

## Smart Query Understanding

### Intent Detection

The system automatically detects what you're looking for:

#### 1. Location Search

**Query:** "Where does it say blessed are the peacemakers?"
**Intent:** Find specific verse location
**Result:** Matthew 5:9

#### 2. Explanation Search

**Query:** "What does it mean to love your enemies?"
**Intent:** Interpretation + context
**Result:** Matthew 5:44 + AI-generated explanation

#### 3. Thematic Search

**Query:** "Show me verses about patience"
**Intent:** Find all verses on theme
**Result:** Galatians 5:22, James 5:7-8, Romans 12:12, etc.

### Language Detection

Automatically detects query language:

```
Query: "love" → Detected: English → Search English translations
Query: "사랑" → Detected: Korean → Search Korean translations
Query: "love and 믿음" → Detected: Mixed → Search both
```

### Query Expansion

System understands related terms:

**Query:** "salvation"
**Expanded to include:** redemption, deliverance, being saved, eternal life

**Query:** "Jesus"
**Expanded to include:** Christ, Lord, Son of God, Messiah

---

## Browse & Navigation

### Browse by Book

Navigate through Bible structure:

```
Testament → Book → Chapter → Verse

Old Testament
├── Genesis (50 chapters)
│   ├── Chapter 1 (31 verses)
│   ├── Chapter 2 (25 verses)
│   └── ...
├── Exodus (40 chapters)
└── ...

New Testament
├── Matthew (28 chapters)
├── Mark (16 chapters)
└── ...
```

### Browse by Genre

Filter books by literary genre:

**Old Testament:**
- Law (Torah): Genesis, Exodus, Leviticus, Numbers, Deuteronomy
- History: Joshua, Judges, Ruth, 1-2 Samuel, 1-2 Kings, etc.
- Wisdom: Job, Psalms, Proverbs, Ecclesiastes, Song of Songs
- Prophecy: Isaiah, Jeremiah, Ezekiel, Daniel, Minor Prophets

**New Testament:**
- Gospels: Matthew, Mark, Luke, John
- History: Acts
- Epistles (Paul): Romans, 1-2 Corinthians, Galatians, etc.
- Epistles (General): Hebrews, James, 1-2 Peter, 1-3 John, Jude
- Prophecy: Revelation

---

## Advanced Search Filters

### Filter by Testament

```
Query: "love"
Filter: Testament = "NT" (New Testament only)
Results: John 3:16, 1 John 4:8, 1 Corinthians 13, etc.
```

### Filter by Genre

```
Query: "wisdom"
Filter: Genre = "wisdom"
Results: Proverbs, Ecclesiastes, Job, Psalms (wisdom psalms)
```

### Filter by Specific Books

```
Query: "faith"
Filter: Books = ["Romans", "Hebrews", "James"]
Results: Only verses from these three books
```

### Combine Filters

```
Query: "Jesus healing"
Filters:
  - Testament: NT
  - Genre: gospel
  - Books: ["Matthew", "Mark", "Luke", "John"]
Results: Gospel healing accounts only
```

---

## Usage Examples

### Example 1: Study Prep

**Scenario:** Preparing Sunday school lesson on forgiveness

1. Search: "forgiveness"
2. Select translations: NIV, 개역개정
3. Filter: Testament = NT
4. Review top 10 results
5. Click Matthew 6:14 for details
6. View cross-references → Find related passages
7. Check original Greek for "forgive" (ἀφίημι)

### Example 2: Devotional Reading

**Scenario:** Looking for encouragement

1. Search: "comfort during hard times"
2. View results in Korean (개역개정)
3. Find Psalm 23
4. Enable Hanja display for deeper understanding
5. Save verse for later reference

### Example 3: Sermon Research

**Scenario:** Researching Paul's theology on grace

1. Search: "Paul's teaching on grace"
2. Filter: Books = Paul's epistles
3. View parallel translations (NIV, ESV, NASB)
4. Check original Greek for "grace" (χάρις)
5. Review cross-references
6. Compare usage across different letters
