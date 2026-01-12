# Bible RAG - API Reference

Complete REST API documentation for the Bible RAG system.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Search](#post-apisearch)
  - [Verse Lookup](#get-apiversebookchapterverse)
  - [Thematic Search](#post-apithemes)
  - [List Translations](#get-apitranslations)
  - [List Books](#get-apibooks)
  - [Health Check](#get-health)
- [Code Examples](#code-examples)

---

## Base URL

### Development
```
http://localhost:8000
```

### Production
```
https://api.bible-rag.yourdom ain.com
```

All API endpoints are prefixed with `/api` unless otherwise noted.

---

## Authentication

Currently, the API does not require authentication for public read operations.

**Future:** JWT-based authentication for user-specific features (bookmarks, notes).

---

## Rate Limiting

### Current Limits

**Development:**
- No rate limits

**Production:**
- **Per IP**: 60 requests/minute
- **Per endpoint**: Varies (see endpoint details)

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1641234567
```

### Rate Limit Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again in 30 seconds.",
    "retry_after": 30
  }
}
```

---

## Response Format

### Success Response

All successful responses return JSON with appropriate HTTP status codes.

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": { ... },
  "meta": {
    "timestamp": "2026-01-11T10:30:00Z",
    "version": "1.0"
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/POST request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "query",
      "issue": "Query must be between 1 and 500 characters"
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `TRANSLATION_NOT_FOUND` | 400 | Invalid translation abbreviation |
| `BOOK_NOT_FOUND` | 404 | Book not found |
| `VERSE_NOT_FOUND` | 404 | Verse not found |

---

## Endpoints

### POST /api/search

Performs semantic search across Bible translations.

#### Request

**Headers:**
```http
Content-Type: application/json
```

**Body:**
```json
{
  "query": "사랑과 용서",
  "languages": ["ko", "en"],
  "translations": ["개역개정", "NIV"],
  "include_original": true,
  "max_results": 10,
  "search_type": "semantic",
  "filters": {
    "testament": "both",
    "genre": null,
    "books": null
  }
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (1-500 chars) |
| `languages` | string[] | No | `["en"]` | Language codes: `"en"`, `"ko"` |
| `translations` | string[] | Yes | - | Translation abbreviations |
| `include_original` | boolean | No | `false` | Include Greek/Hebrew text |
| `max_results` | integer | No | `10` | Max results (1-100) |
| `search_type` | string | No | `"semantic"` | `"semantic"` or `"keyword"` |
| `filters.testament` | string | No | `"both"` | `"OT"`, `"NT"`, `"both"` |
| `filters.genre` | string | No | `null` | Filter by genre |
| `filters.books` | string[] | No | `null` | Filter by book abbreviations |

#### Response

**Success (200 OK):**

```json
{
  "query_time_ms": 245,
  "results": [
    {
      "reference": {
        "book": "마태복음",
        "book_en": "Matthew",
        "chapter": 6,
        "verse": 14,
        "id": "a1b2c3d4-..."
      },
      "translations": {
        "ko": "너희가 사람의 잘못을 용서하면 너희 하늘 아버지께서도 너희 잘못을 용서하시려니와",
        "en": "For if you forgive other people when they sin against you, your heavenly Father will also forgive you."
      },
      "original": {
        "language": "greek",
        "text": "Ἐὰν γὰρ ἀφῆτε τοῖς ἀνθρώποις τὰ παραπτώματα αὐτῶν",
        "strongs": ["G1437", "G1063", "G863", "G3588", "G444"],
        "transliteration": "Ean gar aphēte tois anthrōpois ta paraptōmata autōn"
      },
      "relevance_score": 0.94,
      "cross_references": [
        {
          "book": "마가복음",
          "book_en": "Mark",
          "chapter": 11,
          "verse": 25
        },
        {
          "book": "누가복음",
          "book_en": "Luke",
          "chapter": 6,
          "verse": 37
        }
      ]
    }
  ],
  "ai_response": "Based on these passages, Jesus teaches that forgiveness is reciprocal...",
  "search_metadata": {
    "total_results": 47,
    "embedding_model": "multilingual-e5-large",
    "generation_model": "gemini-2.5-flash",
    "cached": false
  }
}
```

**Error (400 Bad Request):**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "query": "Query must be between 1 and 500 characters",
      "translations": "At least one translation is required"
    }
  }
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "love and forgiveness",
    "languages": ["en"],
    "translations": ["NIV"],
    "max_results": 5
  }'
```

---

### GET /api/verse/{book}/{chapter}/{verse}

Retrieves a specific verse in multiple translations.

#### Request

**Path Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `book` | string | Book abbreviation or name | `John`, `요한복음` |
| `chapter` | integer | Chapter number | `3` |
| `verse` | integer | Verse number | `16` |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `translations` | string | No | All | Comma-separated abbreviations |
| `include_original` | boolean | No | `false` | Include Greek/Hebrew |
| `include_cross_refs` | boolean | No | `true` | Include cross-references |

#### Response

**Success (200 OK):**

```json
{
  "reference": {
    "book": "John",
    "book_korean": "요한복음",
    "chapter": 3,
    "verse": 16,
    "testament": "NT",
    "genre": "gospel"
  },
  "translations": {
    "NIV": "For God so loved the world that he gave his one and only Son...",
    "ESV": "For God so loved the world, that he gave his only Son...",
    "개역개정": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니...",
    "개역한글": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니..."
  },
  "original": {
    "language": "greek",
    "text": "οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον",
    "words": [
      {
        "word": "ἠγάπησεν",
        "transliteration": "ēgapēsen",
        "strongs": "G25",
        "morphology": "V-AAI-3S",
        "definition": "to love, have affection for"
      }
    ]
  },
  "cross_references": [
    {
      "book": "1 John",
      "chapter": 4,
      "verse": 9,
      "relationship": "thematic",
      "text_preview": "This is how God showed his love..."
    }
  ],
  "context": {
    "previous_verse": {
      "chapter": 3,
      "verse": 15,
      "text": "..."
    },
    "next_verse": {
      "chapter": 3,
      "verse": 17,
      "text": "..."
    }
  }
}
```

**Error (404 Not Found):**

```json
{
  "error": {
    "code": "VERSE_NOT_FOUND",
    "message": "Verse not found",
    "details": {
      "book": "John",
      "chapter": 3,
      "verse": 999
    }
  }
}
```

#### cURL Example

```bash
curl "http://localhost:8000/api/verse/John/3/16?translations=NIV,개역개정&include_original=true"
```

---

### POST /api/themes

Performs thematic search across Bible.

#### Request

**Body:**

```json
{
  "theme": "covenant",
  "testament": "both",
  "languages": ["en", "ko"],
  "translations": ["NIV", "개역개정"],
  "max_results": 20
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `theme` | string | Yes | - | Theme keyword |
| `testament` | string | No | `"both"` | `"OT"`, `"NT"`, `"both"` |
| `languages` | string[] | No | `["en"]` | Language codes |
| `translations` | string[] | Yes | - | Translation abbreviations |
| `max_results` | integer | No | `20` | Max results (1-100) |

#### Response

**Success (200 OK):**

```json
{
  "theme": "covenant",
  "results": [
    {
      "reference": {...},
      "translations": {...},
      "relevance_score": 0.91,
      "theme_keywords": ["covenant", "promise", "testament"]
    }
  ],
  "related_themes": ["promise", "agreement", "testament"],
  "total_results": 156
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/api/themes \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "faith",
    "testament": "NT",
    "translations": ["NIV"]
  }'
```

---

### GET /api/translations

Lists all available Bible translations.

#### Request

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `language` | string | No | All | Filter by language code |

#### Response

**Success (200 OK):**

```json
{
  "translations": [
    {
      "id": "a1b2c3d4-...",
      "name": "New International Version",
      "abbreviation": "NIV",
      "language_code": "en",
      "language_name": "English",
      "description": "Contemporary English translation...",
      "is_original_language": false,
      "verse_count": 31102
    },
    {
      "id": "b2c3d4e5-...",
      "name": "개역개정",
      "abbreviation": "RKV",
      "language_code": "ko",
      "language_name": "한국어",
      "description": "Revised Korean Version...",
      "is_original_language": false,
      "verse_count": 31103
    },
    {
      "id": "c3d4e5f6-...",
      "name": "SBL Greek New Testament",
      "abbreviation": "SBLGNT",
      "language_code": "gr",
      "language_name": "Greek",
      "description": "Koine Greek New Testament...",
      "is_original_language": true,
      "verse_count": 7957
    }
  ],
  "total_count": 8
}
```

#### cURL Example

```bash
# Get all translations
curl http://localhost:8000/api/translations

# Get only Korean translations
curl "http://localhost:8000/api/translations?language=ko"
```

---

### GET /api/books

Lists all Bible books with metadata.

#### Request

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `testament` | string | No | All | Filter: `"OT"`, `"NT"` |
| `genre` | string | No | All | Filter by genre |

#### Response

**Success (200 OK):**

```json
{
  "books": [
    {
      "id": "d4e5f6g7-...",
      "name": "Genesis",
      "name_korean": "창세기",
      "abbreviation": "Gen",
      "testament": "OT",
      "genre": "law",
      "book_number": 1,
      "total_chapters": 50,
      "total_verses": 1533
    },
    {
      "id": "e5f6g7h8-...",
      "name": "John",
      "name_korean": "요한복음",
      "abbreviation": "John",
      "testament": "NT",
      "genre": "gospel",
      "book_number": 43,
      "total_chapters": 21,
      "total_verses": 879
    }
  ],
  "total_count": 66
}
```

#### cURL Example

```bash
# Get all books
curl http://localhost:8000/api/books

# Get only NT books
curl "http://localhost:8000/api/books?testament=NT"

# Get only gospels
curl "http://localhost:8000/api/books?genre=gospel"
```

---

### GET /health

Health check endpoint for monitoring.

#### Request

No parameters required.

#### Response

**Success (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-11T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "embedding_model": "loaded"
  },
  "stats": {
    "total_verses": 31103,
    "total_translations": 8,
    "cache_hit_rate": 0.67
  }
}
```

**Error (503 Service Unavailable):**

```json
{
  "status": "unhealthy",
  "timestamp": "2026-01-11T10:30:00Z",
  "services": {
    "database": "unhealthy",
    "redis": "healthy",
    "embedding_model": "error"
  },
  "errors": [
    "Database connection failed",
    "Embedding model not loaded"
  ]
}
```

#### cURL Example

```bash
curl http://localhost:8000/health
```

---

## Code Examples

### JavaScript (Axios)

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Search for verses
async function searchVerses(query, translations = ['NIV']) {
  try {
    const response = await axios.post(`${API_BASE}/api/search`, {
      query,
      languages: ['en'],
      translations,
      max_results: 10
    });
    return response.data;
  } catch (error) {
    console.error('Search error:', error.response?.data || error.message);
    throw error;
  }
}

// Get specific verse
async function getVerse(book, chapter, verse, translations = 'NIV') {
  try {
    const response = await axios.get(
      `${API_BASE}/api/verse/${book}/${chapter}/${verse}`,
      { params: { translations, include_original: true } }
    );
    return response.data;
  } catch (error) {
    console.error('Verse lookup error:', error.response?.data || error.message);
    throw error;
  }
}

// Usage
const results = await searchVerses('love and forgiveness', ['NIV', '개역개정']);
const verse = await getVerse('John', 3, 16, 'NIV,ESV');
```

### Python (requests)

```python
import requests

API_BASE = 'http://localhost:8000'

def search_verses(query: str, translations: list[str] = None):
    """Search for verses semantically."""
    if translations is None:
        translations = ['NIV']

    response = requests.post(
        f'{API_BASE}/api/search',
        json={
            'query': query,
            'languages': ['en'],
            'translations': translations,
            'max_results': 10
        }
    )
    response.raise_for_status()
    return response.json()

def get_verse(book: str, chapter: int, verse: int, translations: str = 'NIV'):
    """Get specific verse in multiple translations."""
    response = requests.get(
        f'{API_BASE}/api/verse/{book}/{chapter}/{verse}',
        params={
            'translations': translations,
            'include_original': True
        }
    )
    response.raise_for_status()
    return response.json()

# Usage
results = search_verses('love and forgiveness', ['NIV', '개역개정'])
verse = get_verse('John', 3, 16, 'NIV,ESV')
```

### TypeScript (fetch)

```typescript
interface SearchRequest {
  query: string;
  languages: string[];
  translations: string[];
  include_original?: boolean;
  max_results?: number;
}

interface SearchResponse {
  query_time_ms: number;
  results: Array<{
    reference: {
      book: string;
      chapter: number;
      verse: number;
    };
    translations: Record<string, string>;
    relevance_score: number;
  }>;
}

const API_BASE = 'http://localhost:8000';

async function searchVerses(request: SearchRequest): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }

  return response.json();
}

// Usage
const results = await searchVerses({
  query: '사랑과 용서',
  languages: ['ko', 'en'],
  translations: ['개역개정', 'NIV'],
  max_results: 10,
});
```

### cURL

```bash
# Search verses
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "love and forgiveness",
    "languages": ["en"],
    "translations": ["NIV"],
    "max_results": 5
  }' | jq

# Get verse
curl "http://localhost:8000/api/verse/John/3/16?translations=NIV,ESV" | jq

# List translations
curl http://localhost:8000/api/translations?language=ko | jq

# Health check
curl http://localhost:8000/health | jq
```

---

## WebSocket Support (Future)

For real-time features (future implementation):

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Search update:', data);
};

ws.send(JSON.stringify({
  action: 'search',
  query: 'love',
  translations: ['NIV']
}));
```

---

## SDK Libraries (Future)

Planned official SDKs:
- **JavaScript/TypeScript**: `@bible-rag/client`
- **Python**: `bible-rag-client`
- **React Hooks**: `@bible-rag/react`
