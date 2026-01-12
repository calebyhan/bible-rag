# Bible RAG - System Architecture

Comprehensive technical architecture documentation for the Bible RAG system.

## Table of Contents

- [System Overview](#system-overview)
- [RAG Workflow](#rag-workflow)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Embedding Strategy](#embedding-strategy)
- [Vector Search Implementation](#vector-search-implementation)
- [Caching Architecture](#caching-architecture)
- [Rate Limiting & Fallbacks](#rate-limiting--fallbacks)
- [Scalability Considerations](#scalability-considerations)
- [Performance Optimization](#performance-optimization)

---

## System Overview

### High-Level Architecture

```mermaid
graph TB
    User["User Layer<br/>(Browser / Mobile Device)"]
    
    subgraph Frontend["Frontend Layer<br/>Next.js 16 + TypeScript 5.9"]
        SearchUI["Search UI<br/>Component"]
        VerseView["Verse View<br/>Component"]
        TransSelector["Translation<br/>Selector"]
    end
    
    subgraph Backend["Backend Layer<br/>FastAPI + Python 3.14"]
        API["API Endpoints<br/>/api/search /api/verse /api/translations"]
        
        subgraph SearchEngine["Semantic Search Engine"]
            QueryEmbed["Query<br/>Embedding"]
            VectorSearch["Vector<br/>Search"]
            LLMGen["LLM<br/>Generation"]
            QueryEmbed --> VectorSearch
            VectorSearch --> LLMGen
        end
        
        API --> SearchEngine
    end
    
    subgraph Database["Database Layer<br/>PostgreSQL 16 + pgvector"]
        VersesTable["Verses Table"]
        EmbedTable["Embeddings Table"]
        CrossRefs["Cross-refs Table"]
        OrigWords["Original Words"]
    end
    
    subgraph Cache["Cache Layer<br/>Redis 7"]
        QueryCache["Query Cache"]
        EmbedCache["Embedding Cache"]
    end
    
    subgraph External["External Services"]
        LLM1["Google Gemini 2.5 Flash (Primary)"]
        LLM2["Groq Llama 3.3 70B (Fallback)"]
    end
    
    User --> Frontend
    Frontend -->|HTTP/REST| Backend
    Backend --> Database
    Backend --> Cache
    Backend --> External
```

### Design Principles

1. **Separation of Concerns**: Clear boundaries between presentation, business logic, and data layers
2. **Stateless Backend**: All requests are independent, enabling horizontal scaling
3. **Caching-First**: Multi-layer caching to minimize database queries and API calls
4. **Graceful Degradation**: Fallback mechanisms for external service failures
5. **Korean-First UX**: Typography, fonts, and text handling optimized for Korean users
6. **Self-Hosted Embeddings**: No rate limits, one-time processing, complete control

---

## RAG Workflow

### Complete Search Flow

```mermaid
flowchart TD
    A["1. User Query<br/>사랑에 대한 예수님의 말씀<br/>(Jesus' teaching about love)"]
    
    B["2. Language Detection & Preprocessing<br/>- Detect: Korean (ko)<br/>- Normalize: Unicode NFC<br/>- Lowercase: context-aware"]
    
    C["3. Cache Check (Redis)<br/>Key: hash(query + translations)<br/>Hit? → Return cached results < 50ms<br/>Miss? → Continue to step 4"]
    
    D["4. Query Embedding<br/>Model: multilingual-e5-large (self-hosted)<br/>Input: 사랑에 대한 예수님의 말씀<br/>Output: 1024-dim vector [0.12, -0.34, 0.56, ...]<br/>Time: ~50-100ms (CPU)"]
    
    E["5. Vector Similarity Search<br/>(PostgreSQL + pgvector)<br/>SELECT verse_id, text,<br/>1 - (vector <=> query_vector) AS score<br/>FROM embeddings JOIN verses<br/>Index: ivfflat (lists=100)<br/>Time: ~200-500ms for 31K vectors"]
    
    F["6. Retrieve Context<br/>Top 10 verses (scores: 0.92, 0.89, 0.85, ...)<br/>For each verse:<br/>- Fetch translations (NIV, 개역개정, etc.)<br/>- Fetch cross-references<br/>- Fetch original language data<br/>Time: ~100-200ms (with indexes)"]
    
    G["7. LLM Generation (Optional)<br/>Provider: Gemini 2.5 Flash (or Groq fallback)<br/>Prompt: Based on these verses: [context]<br/>Output: Contextual explanation in Korean<br/>Time: ~500-1500ms<br/>Rate limit: 10 RPM (Gemini)"]
    
    H["8. Format Response<br/>{<br/>  results: [...],<br/>  ai_response: ...,<br/>  query_time_ms: 1245,<br/>  translations: {...}<br/>}"]
    
    I["9. Cache Result (Redis)<br/>TTL: 24 hours<br/>Increment hit_count for analytics"]
    
    J["10. Return to Frontend<br/>Display results with:<br/>- Verse cards with translations<br/>- Relevance scores<br/>- Cross-reference chips<br/>- Original language expansion"]
    
    A --> B
    B --> C
    C -->|Cache miss| D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
```

**Total Time Breakdown:**
- **Cached query**: 50-100ms
- **Cold query (no cache)**: 1-2 seconds
  - Embedding: 50-100ms
  - Vector search: 200-500ms
  - Context retrieval: 100-200ms
  - LLM generation: 500-1500ms
  - Formatting & caching: 50-100ms

---

## Component Architecture

### Backend Components

#### 1. FastAPI Application (`backend/main.py`)

**Responsibilities:**
- Route handling and request validation
- CORS configuration
- Middleware (logging, error handling)
- Startup/shutdown events (load embedding model)

**Key Endpoints:**
```python
@app.post("/api/search")
async def search_bible(request: SearchRequest) -> SearchResponse:
    # Semantic search with RAG

@app.get("/api/verse/{book}/{chapter}/{verse}")
async def get_verse(...) -> VerseResponse:
    # Fetch specific verse with translations

@app.post("/api/themes")
async def thematic_search(...) -> ThemeResponse:
    # Search by theme/topic

@app.get("/api/translations")
async def list_translations() -> List[Translation]:
    # Get available translations
```

#### 2. Embedding Module (`backend/embeddings.py`)

**Responsibilities:**
- Load self-hosted sentence-transformers model
- Generate embeddings for verses (one-time)
- Generate embeddings for queries (runtime)
- Model caching in memory

**Implementation:**
```python
from sentence_transformers import SentenceTransformer
from functools import lru_cache

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load model once and cache in memory."""
    return SentenceTransformer('intfloat/multilingual-e5-large')

def embed_text(text: str) -> np.ndarray:
    """Generate 1024-dim embedding for text."""
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True)
```

**Model Specifications:**
- Name: `intfloat/multilingual-e5-large`
- Dimensions: 1024
- Max sequence length: 512 tokens
- Languages: 100+ (optimized for English, Korean, Chinese, Spanish)
- Size: ~2GB download
- Performance: ~50-100 verses/second on modern CPU

#### 3. Vector Search Module (`backend/search.py`)

**Responsibilities:**
- Execute cosine similarity search in PostgreSQL
- Filter by translation, testament, genre
- Sort by relevance score
- Pagination support

**SQL Query:**
```sql
SELECT
    v.id, v.text, v.chapter, v.verse,
    b.name, b.testament,
    1 - (e.vector <=> $1::vector) AS similarity_score
FROM embeddings e
JOIN verses v ON e.verse_id = v.id
JOIN books b ON v.book_id = b.id
WHERE v.translation_id = ANY($2::uuid[])
  AND (1 - (e.vector <=> $1::vector)) > 0.7  -- Similarity threshold
ORDER BY e.vector <=> $1::vector  -- Cosine distance (ascending)
LIMIT $3
```

**Index Strategy:**
- ivfflat index on `embeddings.vector`
- `lists` parameter: 100 (optimal for 31K vectors)
- Index build time: 5-10 minutes (one-time)
- Search time: O(log n) with index

#### 4. Cache Module (`backend/cache.py`)

**Responsibilities:**
- Query result caching
- Embedding caching for common queries
- Cache invalidation and TTL management
- Hit count analytics

**Cache Layers:**
```python
# Layer 1: In-memory (LRU cache)
@lru_cache(maxsize=1000)
def get_cached_embedding(query: str) -> np.ndarray:
    return embed_text(query)

# Layer 2: Redis (query results)
def cache_search_results(
    query_hash: str,
    results: dict,
    ttl: int = 86400  # 24 hours
):
    redis_client.setex(query_hash, ttl, json.dumps(results))
```

**Cache Keys:**
```python
query_hash = hashlib.md5(
    f"{query}:{','.join(sorted(translations))}:{filters}".encode()
).hexdigest()
```

#### 5. Database Module (`backend/database.py`)

**Responsibilities:**
- SQLAlchemy ORM models
- Database connection pooling
- Query builders
- Migration support (Alembic)

**Models:**
```python
class Translation(Base):
    __tablename__ = "translations"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    abbreviation: Mapped[str]
    language_code: Mapped[str]
    verses: Mapped[List["Verse"]] = relationship(back_populates="translation")

class Verse(Base):
    __tablename__ = "verses"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    translation_id: Mapped[UUID] = mapped_column(ForeignKey("translations.id"))
    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id"))
    chapter: Mapped[int]
    verse: Mapped[int]
    text: Mapped[str]
    embedding: Mapped["Embedding"] = relationship(back_populates="verse")

class Embedding(Base):
    __tablename__ = "embeddings"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    verse_id: Mapped[UUID] = mapped_column(ForeignKey("verses.id"))
    vector: Mapped[Vector] = mapped_column(Vector(1024))  # pgvector type
    model_version: Mapped[str]
```

### Frontend Components

#### 1. Search Interface (`frontend/src/app/page.tsx`)

**Features:**
- Auto-detecting language (English/Korean)
- Real-time search suggestions
- Translation selector
- Filter options (testament, genre)

#### 2. Verse Display (`frontend/src/components/VerseCard.tsx`)

**Features:**
- Parallel translation view
- Expandable original language
- Cross-reference navigation
- Copy/share functionality

#### 3. Korean Optimization (`frontend/src/components/KoreanToggle.tsx`)

**Features:**
- Hanja (한자) display toggle
- Romanization (로마자) display
- Font size adjustment
- Line height optimization (1.8-2.0)

---

## Data Flow

### Data Ingestion Flow

```
1. Bible API/Dataset
   ↓
2. Fetch & Parse (data_ingestion.py)
   ├─ Normalize text (Unicode NFC for Korean)
   ├─ Parse book/chapter/verse structure
   └─ Extract metadata (testament, genre)
   ↓
3. Database Insert
   ├─ translations table
   ├─ books table
   └─ verses table (31,000+ rows)
   ↓
4. Embedding Generation (embeddings.py)
   ├─ Load multilingual-e5-large model
   ├─ Batch process (32 verses at a time)
   ├─ Generate 1024-dim vectors
   └─ Insert into embeddings table
   ↓
5. Index Creation
   ├─ CREATE INDEX ... USING ivfflat
   └─ Build cross-reference links
   ↓
6. Ready for Queries
```

### Query Flow

```
User Input
   ↓
Frontend (Next.js)
   ├─ Validate input
   ├─ Detect language
   └─ Send POST /api/search
   ↓
Backend API (FastAPI)
   ├─ Check Redis cache
   ├─ [Cache miss] → Generate query embedding
   ├─ Vector similarity search (PostgreSQL)
   ├─ Retrieve context (verses, translations, cross-refs)
   ├─ [Optional] LLM generation (Gemini/Groq)
   ├─ Format response
   └─ Cache result (Redis)
   ↓
Frontend Display
   ├─ Render verse cards
   ├─ Display translations
   ├─ Show cross-references
   └─ Expandable original language
```

---

## Embedding Strategy

### Model Selection Rationale

**Why multilingual-e5-large?**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Multilingual Support | 10/10 | 100+ languages, excellent Korean |
| Korean Quality | 10/10 | Trained on Korean corpus |
| English Quality | 9/10 | SOTA on English benchmarks |
| Embedding Dimension | 9/10 | 1024-dim (high quality) |
| Self-Hostable | 10/10 | No API, no rate limits |
| Model Size | 8/10 | 2GB (manageable) |
| CPU Performance | 9/10 | 50-100 verses/sec on modern CPU |
| GPU Performance | 10/10 | 500+ verses/sec on mid-range GPU |

**Alternatives Considered:**
- `all-mpnet-base-v2`: English-only, lower dimension (768)
- `paraphrase-multilingual-mpnet-base-v2`: Slower, lower quality
- OpenAI text-embedding-3-large: API costs, rate limits

### Embedding Generation

**Batch Processing:**
```python
batch_size = 32  # Optimal for CPU
for i in range(0, len(verses), batch_size):
    batch_texts = verses[i:i+batch_size]
    embeddings = model.encode(
        batch_texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True  # For cosine similarity
    )
    # Insert into database
```

**Performance:**
- CPU (M1 Mac): ~100 verses/second → 31,000 verses in ~5 minutes
- CPU (Intel i7): ~50 verses/second → 31,000 verses in ~10 minutes
- GPU (NVIDIA RTX 3060): ~500 verses/second → 31,000 verses in ~1 minute

### Normalization

All embeddings are L2-normalized for cosine similarity:
```python
embedding = embedding / np.linalg.norm(embedding)
```

This allows using efficient dot product instead of full cosine calculation:
```
cosine_similarity(a, b) = dot(a, b) / (||a|| * ||b||)
# With normalized vectors: ||a|| = ||b|| = 1
cosine_similarity(a, b) = dot(a, b)
```

---

## Vector Search Implementation

### pgvector Index

**Index Type:** ivfflat (Inverted File with Flat compression)

**Creation:**
```sql
CREATE INDEX idx_embeddings_vector
ON embeddings
USING ivfflat (vector vector_cosine_ops)
WITH (lists = 100);
```

**Parameters:**
- `lists = 100`: Number of clusters (√N for N=31K)
- `vector_cosine_ops`: Cosine distance operator

**Trade-offs:**
- More lists → Faster build, slower search
- Fewer lists → Slower build, faster search
- Optimal for 31K vectors: 100-150 lists

### Distance Metrics

**pgvector supports:**
- `<->`: L2 distance (Euclidean)
- `<#>`: Inner product
- `<=>`: Cosine distance (1 - cosine similarity)

**We use cosine distance (`<=>`):**
```sql
-- Distance: 0 (identical) to 2 (opposite)
SELECT 1 - (vector <=> query_vector) AS similarity
FROM embeddings
ORDER BY vector <=> query_vector
LIMIT 10;
```

### Search Performance

| Vectors | Index | Search Time | Recall@10 |
|---------|-------|-------------|-----------|
| 31,000 | ivfflat (100) | 200-500ms | 95%+ |
| 31,000 | No index (seq scan) | 3-5s | 100% |
| 100,000 | ivfflat (316) | 500-800ms | 95%+ |

**Recall:** Percentage of true top-K results found (vs. exact search)

---

## Caching Architecture

### Multi-Layer Cache

```
Request
   ↓
┌──────────────────────────────┐
│ Layer 1: In-Memory (Python)  │
│ - LRU cache (1000 items)     │
│ - Query embeddings           │
│ - Model instance             │
│ - Hit time: < 1ms            │
└──────────┬───────────────────┘
           │ Cache miss
           ↓
┌──────────────────────────────┐
│ Layer 2: Redis               │
│ - Query results (24h TTL)    │
│ - Common queries             │
│ - Hit time: 10-50ms          │
└──────────┬───────────────────┘
           │ Cache miss
           ↓
┌──────────────────────────────┐
│ Layer 3: Database Query      │
│ - Vector search              │
│ - Context retrieval          │
│ - Hit time: 200-500ms        │
└──────────────────────────────┘
```

### Cache Invalidation

**Strategies:**
- **Time-based (TTL)**: 24 hours for query results
- **Event-based**: Invalidate on translation updates
- **LRU eviction**: Automatic for in-memory cache

**Cache Key Design:**
```python
def generate_cache_key(
    query: str,
    translations: List[str],
    filters: dict
) -> str:
    key_data = {
        "query": query.lower().strip(),
        "translations": sorted(translations),
        "filters": filters
    }
    return hashlib.md5(
        json.dumps(key_data, sort_keys=True).encode()
    ).hexdigest()
```

### Cache Analytics

**Tracked metrics:**
- Hit rate: `cache_hits / (cache_hits + cache_misses)`
- Popular queries: `ORDER BY hit_count DESC LIMIT 100`
- Cache size: `redis-cli INFO memory`

---

## Rate Limiting & Fallbacks

### LLM API Rate Limits

**Gemini 2.5 Flash (Primary):**
- 10 RPM (requests per minute)
- 20 RPD (requests per day)
- Free tier

**Groq Llama 3.3 70B (Fallback):**
- 30 RPM
- Free tier

### Fallback Strategy

```python
async def generate_response(context: str, query: str) -> str:
    try:
        # Try Gemini first
        response = await call_gemini(context, query)
        return response
    except RateLimitError:
        logger.warning("Gemini rate limit hit, falling back to Groq")
        try:
            response = await call_groq(context, query)
            return response
        except RateLimitError:
            logger.error("Both LLM services rate limited")
            # Return results without AI-generated response
            return None
```

### Rate Limiter Implementation

```python
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = deque()

    async def acquire(self):
        now = datetime.now()
        # Remove old requests outside window
        while self.requests and now - self.requests[0] > self.window:
            self.requests.popleft()

        if len(self.requests) >= self.max_requests:
            # Rate limited
            wait_time = (self.requests[0] + self.window - now).total_seconds()
            raise RateLimitError(f"Wait {wait_time:.1f}s")

        self.requests.append(now)

# Usage
gemini_limiter = RateLimiter(max_requests=10, window_seconds=60)
groq_limiter = RateLimiter(max_requests=30, window_seconds=60)
```

---

## Scalability Considerations

### Horizontal Scaling

**Stateless Backend:**
- FastAPI servers are stateless
- Can scale to N instances behind load balancer
- Session data stored in Redis (shared)

**Load Balancing:**
```nginx
upstream bible_rag_backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://bible_rag_backend;
    }
}
```

### Database Scaling

**Read Replicas:**
- Primary: Write operations (rare: admin updates)
- Replicas: Read operations (search queries)
- Connection pooling: 20 connections per instance

**Partitioning Strategies:**
- Partition by translation (NIV, ESV, 개역개정)
- Partition by testament (OT, NT)
- Not needed until 1M+ verses

### Redis Scaling

**Redis Cluster:**
- Shard by cache key hash
- 3-node cluster for high availability
- Automatic failover

**Memory Management:**
- Max memory: 4GB
- Eviction policy: `allkeys-lru`
- TTL: 24 hours for query cache

### Cost-Efficient Scaling

**Free Tier Limits:**
- Supabase: 500MB DB (sufficient for 100K+ verses)
- Vercel: 100GB bandwidth/month
- Upstash Redis: 10K commands/day

**Paid Scaling Path:**
- Supabase Pro ($25/mo): 8GB DB, more connections
- Railway: $5/month credit for backend
- Upstash Pay-as-you-go: $0.20/100K commands

---

## Performance Optimization

### Backend Optimizations

1. **Connection Pooling:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

2. **Async I/O:**
```python
@app.post("/api/search")
async def search(request: SearchRequest):
    # Parallel execution
    results = await asyncio.gather(
        fetch_verses(query),
        fetch_cross_references(verse_ids),
        fetch_original_language(verse_ids)
    )
```

3. **Batch Processing:**
```python
# Fetch multiple verses in one query
verses = session.query(Verse).filter(
    Verse.id.in_(verse_ids)
).all()
```

### Frontend Optimizations

1. **Code Splitting:**
```typescript
// Next.js automatic code splitting by route
const VerseDetail = dynamic(() => import('@/components/VerseDetail'))
```

2. **Image Optimization:**
```typescript
import Image from 'next/image'
// Automatic WebP conversion, lazy loading
<Image src="/logo.png" width={200} height={200} alt="Logo" />
```

3. **Font Optimization:**
```typescript
import { Noto_Sans_KR } from 'next/font/google'
const notoSansKr = Noto_Sans_KR({ subsets: ['korean'] })
// Automatic font subsetting
```

### Database Optimizations

1. **Indexes:**
```sql
CREATE INDEX idx_verses_book_chapter ON verses(book_id, chapter);
CREATE INDEX idx_verses_translation ON verses(translation_id);
CREATE INDEX idx_cross_refs_verse ON cross_references(verse_id);
```

2. **Query Optimization:**
```sql
-- Use EXISTS instead of COUNT for boolean checks
SELECT EXISTS(SELECT 1 FROM verses WHERE id = $1);

-- Use LIMIT for pagination
SELECT * FROM verses ORDER BY id OFFSET $1 LIMIT $2;
```

3. **Materialized Views (future):**
```sql
-- Pre-aggregate popular queries
CREATE MATERIALIZED VIEW popular_verses AS
SELECT verse_id, COUNT(*) as view_count
FROM query_cache
GROUP BY verse_id
ORDER BY view_count DESC
LIMIT 100;
```

---

## Security Considerations

### API Security

1. **Rate Limiting:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/search")
@limiter.limit("10/minute")
async def search(...):
    pass
```

2. **Input Validation:**
```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    translations: List[str] = Field(..., min_items=1, max_items=10)
    max_results: int = Field(10, ge=1, le=100)
```

3. **CORS Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Database Security

1. **SQL Injection Prevention:**
```python
# Use parameterized queries (SQLAlchemy ORM)
verses = session.query(Verse).filter(
    Verse.id == verse_id  # NOT f"... WHERE id = {verse_id}"
).all()
```

2. **Connection Security:**
```python
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"
```

3. **Secrets Management:**
```python
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Never hardcode
```
