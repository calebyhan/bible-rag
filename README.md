# Bible RAG

> A multilingual Bible study platform powered by semantic search, supporting English and Korean with deep integration of original biblical languages.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue)](https://www.typescriptlang.org/)
[![Node.js 24 LTS](https://img.shields.io/badge/Node.js-24_LTS-green)](https://nodejs.org/)

## Overview

Bible RAG is a Retrieval-Augmented Generation (RAG) system that transforms Bible study through intelligent semantic search. Ask natural questions in English or Korean and receive contextually relevant passages with cross-translation comparisons, original language insights, and AI-powered interpretations.

### Key Features

- **Semantic Search**: Natural language queries in English or Korean
  - "What does Jesus say about forgiveness?"
  - "용서에 대한 예수님의 말씀"
  - Handles code-switching: "요한복음에서 love에 대한 구절"

- **Multi-Translation Support**
  - **English**: NIV, ESV, NASB
  - **Korean**: 개역개정, 개역한글, 새번역, 공동번역
  - **Original Languages**: Hebrew (OT), Greek (NT), Aramaic

- **Parallel Translation View**: Compare verses side-by-side across translations

- **Original Language Integration**
  - Strong's Concordance numbers (G1-G5624, H1-H8674)
  - Morphological parsing (tense, voice, mood, case)
  - Transliteration and pronunciation guides

- **Cross-Reference Discovery**: Automatically surface related passages, prophecy-fulfillment connections, and quotations

- **Korean-Specific Features**
  - Hanja (한자) display for theological terms
  - Romanization for pronunciation
  - Optimized Korean typography (Noto Sans KR, 나눔고딕)
  - Respectful honorific language handling

- **Theological Term Glossary**: Multilingual term mapping
  ```
  속죄 (sokjoe) = Atonement = כָּפַר (kaphar, H3722)
  구원 (guwon) = Salvation = σωτηρία (soteria, G4991)
  은혜 (eunhye) = Grace = χάρις (charis, G5485)
  ```

- **Smart Query Understanding**: Automatic intent detection and language recognition

## Tech Stack

### Backend
- **FastAPI** (Python 3.14) - High-performance API server
- **PostgreSQL + pgvector** - Vector similarity search
- **Redis** - Query caching and performance optimization
- **multilingual-e5-large** - Self-hosted embedding model (1024-dim)
- **Google Gemini 2.5 Flash** - LLM for contextual responses (with Groq fallback)

### Frontend
- **Next.js 16** - React framework with Turbopack bundler
- **TypeScript 5.9** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Noto Sans KR** - Optimized Korean font support

### Deployment
- **Development**: Local PostgreSQL, Redis, FastAPI, Next.js
- **Production**: Supabase (database), Vercel (frontend), Railway/Vercel (backend)

## Quick Start

### Prerequisites
- Python 3.14+ (or Python 3.12+)
- Node.js 24 LTS (or Node.js 22 LTS)
- Docker & Docker Compose
- 8GB RAM minimum (16GB recommended)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bible-rag.git
   cd bible-rag
   ```

2. **Start local infrastructure**
   ```bash
   docker-compose up -d  # Starts PostgreSQL + Redis
   ```

3. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env  # Configure your environment variables
   python data_ingestion.py  # Ingest Bible data
   python embeddings.py  # Generate embeddings (15-30 min one-time)
   uvicorn main:app --reload  # Start API server at http://localhost:8000
   ```

4. **Frontend setup**
   ```bash
   cd ../frontend
   npm install
   cp .env.example .env.local  # Configure environment variables
   npm run dev  # Start Next.js at http://localhost:3000
   ```

5. **Visit the application**
   Open [http://localhost:3000](http://localhost:3000) in your browser

## Example Queries

### English Semantic Search
```
"Jesus teaching about love"
"Where does the Bible talk about faith?"
"What did Paul say about grace?"
```

### Korean Semantic Search
```
"사랑에 대한 예수님의 가르침"
"믿음에 관한 성경 구절"
"바울이 은혜에 대해 말한 것"
```

### Mixed Language Search
```
"요한복음에서 love에 대한 구절"
"Genesis의 creation story"
```

## Project Structure

```
bible-rag/
├── backend/              # FastAPI backend
│   ├── main.py          # API entry point
│   ├── database.py      # SQLAlchemy models
│   ├── embeddings.py    # Embedding generation
│   ├── search.py        # Search logic
│   ├── cache.py         # Redis caching
│   └── data_ingestion.py # Bible data ingestion
├── frontend/            # Next.js frontend
│   └── src/
│       ├── app/         # Next.js pages
│       └── components/  # React components
├── docs/                # Comprehensive documentation
│   ├── ARCHITECTURE.md  # System design
│   ├── DATABASE.md      # Database schema
│   ├── API.md          # API reference
│   ├── SETUP.md        # Detailed setup guide
│   └── DEPLOYMENT.md   # Production deployment
├── docker-compose.yml   # Local development environment
├── README.md           # This file
└── CLAUDE.md           # AI assistant context
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and technical details
- [Database Schema](docs/DATABASE.md) - Complete database documentation
- [API Reference](docs/API.md) - Endpoint specifications
- [Setup Guide](docs/SETUP.md) - Detailed installation instructions
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Features](docs/FEATURES.md) - Comprehensive feature documentation
- [Development Guide](docs/DEVELOPMENT.md) - Contributing guidelines
- [Korean Documentation](docs/KOREAN.md) - 한국어 문서

## API Endpoints

### Search
```
POST /api/search
{
  "query": "사랑과 용서",
  "languages": ["ko", "en"],
  "translations": ["개역개정", "NIV"],
  "include_original": true,
  "max_results": 10
}
```

### Verse Lookup
```
GET /api/verse/{book}/{chapter}/{verse}?translations=NIV,개역개정
```

### Thematic Search
```
POST /api/themes
{
  "theme": "covenant",
  "testament": "both",
  "languages": ["en", "ko"]
}
```

See [API Documentation](docs/API.md) for complete reference.

## Performance

- **Query Response Time**: < 2 seconds for initial search, < 500ms for cached queries
- **Embedding Generation**: ~15-30 minutes one-time setup for full Bible (~31,000 verses)
- **Vector Search**: Uses pgvector with ivfflat indexes for efficient similarity search
- **Caching**: Redis-based multi-layer caching for common queries

## Contributing

We welcome contributions! Please see our [Development Guide](docs/DEVELOPMENT.md) for:
- Code style and conventions
- How to add new features
- Testing guidelines
- Git workflow

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Bible Translations**: NIV, ESV, NASB, 개역개정, and other translations via Bible API and open sources
- **Original Languages**: Open Scripture Hebrew Bible, SBL Greek New Testament
- **Strong's Concordance**: Public domain lexical data
- **Embedding Model**: [intfloat/multilingual-e5-large](https://huggingface.co/intfloat/multilingual-e5-large)
- **LLM**: Google Gemini 2.5 Flash, Groq

---

Made with dedication to multilingual Bible study | [Documentation](docs/) | [API Reference](docs/API.md)
