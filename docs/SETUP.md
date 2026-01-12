# Bible RAG - Setup Guide

Complete installation and configuration guide for local development.

## Table of Contents

- [System Requirements](#system-requirements)
- [Prerequisites Installation](#prerequisites-installation)
- [Local Development Environment](#local-development-environment)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Data Ingestion](#data-ingestion)
- [Embedding Generation](#embedding-generation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware

**Minimum Requirements:**
- CPU: 4+ cores (Intel i5/AMD Ryzen 5 or equivalent)
- RAM: 8GB
- Storage: 20GB free space
- Internet: Stable connection for downloading models and data

**Recommended Requirements:**
- CPU: 8+ cores (Intel i7/AMD Ryzen 7, Apple M1/M2/M3/M4)
- RAM: 16GB
- Storage: 50GB SSD
- GPU: Optional (speeds up embedding 3-5x, but not required)

### Operating Systems

- **macOS**: 12.0+ (Monterey or later)
- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 35+
- **Windows**: Windows 10/11 with WSL2 (recommended) or native

---

## Prerequisites Installation

### 1. Python 3.14+ (or 3.12+)

**macOS (using Homebrew):**
```bash
brew install python@3.14
python3.14 --version  # Verify installation
# Alternative: brew install python@3.12
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.14 python3.14-venv python3.14-dev
python3.14 --version
# Alternative: python3.12
```

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"
- Verify: `python --version`

### 2. Node.js 24 LTS (or 22 LTS)

**macOS:**
```bash
brew install node@24
node --version  # Should be 24.x (LTS)
npm --version
# Alternative: brew install node@22
```

**Linux:**
```bash
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
npm --version
# Alternative: setup_22.x for Node.js 22 LTS
```

**Windows:**
- Download from [nodejs.org](https://nodejs.org/)
- Install LTS version (24.x)
- Verify in PowerShell: `node --version`

### 3. Docker and Docker Compose

**macOS:**
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Or use Homebrew
brew install --cask docker

# Start Docker Desktop application
# Verify installation
docker --version
docker-compose --version
```

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

**Windows:**
- Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- Ensure WSL2 backend is enabled
- Verify in PowerShell: `docker --version`

### 4. Git

**macOS:**
```bash
brew install git
git --version
```

**Linux:**
```bash
sudo apt install git
git --version
```

**Windows:**
- Download from [git-scm.com](https://git-scm.com/)
- Install with default options

---

## Local Development Environment

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/bible-rag.git
cd bible-rag

# Verify directory structure
ls -la
# Should see: backend/, frontend/, docs/, docker-compose.yml, README.md, etc.
```

### 2. Start Infrastructure Services

**Create and start PostgreSQL + Redis:**

```bash
# Start services in detached mode
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                COMMAND                  STATUS
# bible-rag-postgres  "docker-entrypoint.s…"   Up
# bible-rag-redis     "docker-entrypoint.s…"   Up

# Check logs if needed
docker-compose logs postgres
docker-compose logs redis
```

**Default Service Ports:**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

**Stop services when needed:**
```bash
docker-compose down  # Stops and removes containers (data persists in volumes)
docker-compose down -v  # Stops and removes containers AND volumes (deletes all data)
```

### 3. Database Initialization

**Connect to PostgreSQL:**
```bash
# Using psql (if installed locally)
psql -h localhost -p 5432 -U bible_user -d bible_rag
# Password: bible_password (from docker-compose.yml)

# Or using Docker exec
docker exec -it bible-rag-postgres psql -U bible_user -d bible_rag
```

**Enable pgvector extension:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Create initial schema:**
```sql
-- This will be handled by backend/database.py when you run the application
-- But you can verify the database is accessible
\dt  -- List tables (should be empty initially)
\q   -- Quit psql
```

---

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Verify activation (should see (venv) in prompt)
which python  # Should point to venv/bin/python
```

### 2. Install Dependencies

```bash
# Ensure venv is activated (you should see (venv) in your prompt)

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will install:
# - FastAPI, Uvicorn (API server)
# - SQLAlchemy, psycopg2 (database)
# - pgvector (vector extension client)
# - redis (caching)
# - sentence-transformers (embedding model)
# - google-generativeai, groq (LLM APIs)
# - And more...

# Verify key packages
pip list | grep -E "fastapi|sqlalchemy|sentence-transformers"
```

**Expected Installation Time:** 5-10 minutes (downloads ~2GB of packages)

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor (vim, code, etc.)
```

**Update the following variables in `.env`:**

```env
# Database Configuration
DATABASE_URL=postgresql://bible_user:bible_password@localhost:5432/bible_rag
POSTGRES_USER=bible_user
POSTGRES_PASSWORD=bible_password
POSTGRES_DB=bible_rag

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# API Keys (get these from respective services)
GEMINI_API_KEY=your_gemini_api_key_here  # Get from https://ai.google.dev/
GROQ_API_KEY=your_groq_api_key_here      # Get from https://console.groq.com/

# Embedding Model Settings
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DIMENSION=1024

# Cache Settings
CACHE_TTL=86400  # 24 hours in seconds

# Search Settings
MAX_RESULTS_DEFAULT=10
VECTOR_SEARCH_LISTS=100  # ivfflat index parameter
```

**Get API Keys:**

1. **Gemini API Key** (Free):
   - Visit https://ai.google.dev/
   - Sign in with Google account
   - Click "Get API Key"
   - Create new API key
   - Copy and paste into `.env`

2. **Groq API Key** (Free):
   - Visit https://console.groq.com/
   - Sign up for free account
   - Go to API Keys section
   - Create new API key
   - Copy and paste into `.env`

### 4. Initialize Database Schema

```bash
# Ensure venv is activated and you're in backend/ directory
# Ensure PostgreSQL is running (docker-compose up -d)

# Run database initialization
python -c "from database import init_db; init_db()"

# Or create a simple init script
cat > init_db.py << 'EOF'
from database import init_db

if __name__ == "__main__":
    print("Initializing database schema...")
    init_db()
    print("Database initialized successfully!")
EOF

python init_db.py
```

**Verify schema creation:**
```bash
# Connect to database
docker exec -it bible-rag-postgres psql -U bible_user -d bible_rag

# List all tables
\dt

# Expected tables:
# - translations
# - books
# - verses
# - embeddings
# - cross_references
# - original_words
# - query_cache

\q  # Quit
```

### 5. Test Backend Server

```bash
# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

**Test API in another terminal:**
```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status": "healthy"}

# API documentation
open http://localhost:8000/docs  # Opens Swagger UI

# Or visit manually in browser:
# http://localhost:8000/docs - Swagger UI
# http://localhost:8000/redoc - ReDoc
```

---

## Frontend Setup

### 1. Install Dependencies

```bash
# Open new terminal window/tab
cd frontend

# Install Node.js packages
npm install

# This will install:
# - Next.js 14, React 18
# - TypeScript
# - Tailwind CSS
# - Axios (HTTP client)
# - Korean fonts (Noto Sans KR)

# Expected installation time: 2-5 minutes
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env.local

# Edit .env.local
nano .env.local
```

**Update `.env.local`:**
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME=Bible RAG
NEXT_PUBLIC_DEFAULT_LANGUAGE=en
NEXT_PUBLIC_SUPPORTED_LANGUAGES=en,ko

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_ORIGINAL_LANGUAGE=true
NEXT_PUBLIC_ENABLE_CROSS_REFERENCES=true
NEXT_PUBLIC_ENABLE_KOREAN_HANJA=true
```

### 3. Configure Korean Fonts

**Verify Tailwind configuration includes Korean fonts:**

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-noto-sans-kr)', 'system-ui', 'sans-serif'],
        korean: ['Noto Sans KR', '나눔고딕', 'sans-serif'],
      },
      lineHeight: {
        'korean': '1.8',  // Optimized for Korean readability
      },
    },
  },
};
```

### 4. Start Development Server

```bash
# Ensure backend is running in another terminal
# Start Next.js development server
npm run dev

# Expected output:
# > bible-rag-frontend@0.1.0 dev
# > next dev
#
# - ready started server on 0.0.0.0:3000, url: http://localhost:3000
# - event compiled client and server successfully
# - wait compiling...
```

**Access the application:**
- Open browser: http://localhost:3000
- You should see the Bible RAG home page with search bar

---

## Data Ingestion

### Overview
Ingest Bible text from various sources into the database.

### 1. Bible Translation Sources

**English Translations:**
- NIV, ESV, NASB via Bible API (https://scripture.api.bible)
- Public domain: KJV from various sources

**Korean Translations:**
- 개역개정 (Revised Korean Version)
- 개역한글, 새번역, 공동번역
- Sources: Korean Bible Society APIs, open datasets

**Original Languages:**
- Hebrew: Open Scripture Hebrew Bible
- Greek: SBL Greek New Testament, Berean Interlinear
- Strong's Concordance data

### 2. Run Data Ingestion Script

```bash
cd backend
source venv/bin/activate  # Ensure venv is activated

# Run data ingestion
python data_ingestion.py

# Expected process:
# 1. Fetching English translations (NIV, ESV, NASB)...
# 2. Fetching Korean translations (개역개정, etc.)...
# 3. Fetching original language data...
# 4. Parsing and normalizing text...
# 5. Inserting into database...
# 6. Building cross-references...
# 7. Complete! Inserted XX,XXX verses across X translations
```

**Expected Duration:** 10-30 minutes depending on internet speed and data sources

### 3. Verify Data Ingestion

```bash
# Connect to database
docker exec -it bible-rag-postgres psql -U bible_user -d bible_rag

# Check translations
SELECT * FROM translations;

# Check verse count
SELECT t.abbreviation, COUNT(v.id) as verse_count
FROM translations t
LEFT JOIN verses v ON t.id = v.translation_id
GROUP BY t.abbreviation;

# Expected output:
#  abbreviation | verse_count
# --------------+-------------
#  NIV          | 31102
#  ESV          | 31086
#  개역개정      | 31103
#  ...

# Check sample verse
SELECT * FROM verses LIMIT 1;

\q  # Quit
```

---

## Embedding Generation

### Overview
Generate vector embeddings for all verses using the multilingual-e5-large model.

**Important Notes:**
- **One-time process**: Only needs to be run once (or when adding new translations)
- **Duration**: 15-30 minutes for full Bible (~31,000 verses) on modern CPU
- **GPU acceleration**: If you have CUDA GPU, it will be ~3-5 minutes
- **Disk space**: Model download is ~2GB, embeddings storage ~120MB

### 1. Generate Embeddings

```bash
cd backend
source venv/bin/activate

# Run embedding generation
python embeddings.py

# Expected output:
# Loading embedding model 'intfloat/multilingual-e5-large'...
# Downloading model (first run only, ~2GB)...
# Model loaded successfully!
# Fetching verses from database...
# Found 31,103 verses to embed
# Generating embeddings in batches of 32...
# Batch 1/972: Processing verses 1-32... [Progress bar]
# Batch 2/972: Processing verses 33-64... [Progress bar]
# ...
# Embedding generation complete!
# Total time: 23m 15s
# Average: 22.3 verses/second
```

**Progress Indicators:**
- Real-time progress bar
- Estimated time remaining
- Verses processed per second
- Current batch number

### 2. Monitor System Resources

**While embedding generation is running (optional):**

```bash
# Monitor CPU/memory usage
# macOS:
top -o cpu

# Linux:
htop  # or: top

# Check Python process
ps aux | grep python

# Expected resource usage:
# - CPU: 200-400% (utilizing multiple cores)
# - Memory: 4-8GB (model loaded in RAM)
# - Disk I/O: Moderate (writing to database)
```

### 3. Verify Embeddings

```bash
# Connect to database
docker exec -it bible-rag-postgres psql -U bible_user -d bible_rag

# Check embedding count
SELECT COUNT(*) FROM embeddings;
-- Expected: 31,103 (or total verse count)

# Check embedding dimensions
SELECT verse_id, vector_dims(vector) FROM embeddings LIMIT 1;
-- Expected: 1024

# Verify model version
SELECT DISTINCT model_version FROM embeddings;
-- Expected: multilingual-e5-large

\q
```

### 4. Build Vector Index (for Performance)

```bash
# Connect to database
docker exec -it bible-rag-postgres psql -U bible_user -d bible_rag
```

```sql
-- Build ivfflat index for fast similarity search
-- This may take 5-10 minutes for 31K vectors
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
ON embeddings
USING ivfflat (vector vector_cosine_ops)
WITH (lists = 100);

-- Verify index creation
\d embeddings

-- Test similarity search performance
EXPLAIN ANALYZE
SELECT verse_id, 1 - (vector <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM embeddings
ORDER BY vector <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;

\q
```

---

## Verification

### End-to-End Test

**1. Ensure all services are running:**
```bash
# Terminal 1: Check Docker services
docker-compose ps
# Both postgres and redis should be "Up"

# Terminal 2: Backend should be running
# You should see: uvicorn main:app --reload

# Terminal 3: Frontend should be running
# You should see: next dev
```

**2. Test API endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# List translations
curl http://localhost:8000/api/translations

# Search test (with jq for pretty JSON)
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "love and forgiveness",
    "languages": ["en"],
    "translations": ["NIV"],
    "max_results": 5
  }' | jq

# Expected: JSON response with verse results
```

**3. Test frontend:**
1. Open http://localhost:3000
2. Enter search query: "What does Jesus say about love?"
3. Verify:
   - Search executes without errors
   - Results display with verses
   - Translations show correctly
   - Korean text (if selected) renders properly
4. Click on a verse to view details
5. Check cross-references display

**4. Test Korean functionality:**
1. Search: "사랑에 대한 예수님의 말씀"
2. Verify Korean text displays correctly
3. Check Hanja display (if enabled)
4. Test romanization toggle

### Performance Check

**Measure query response time:**
```bash
# Install hey (HTTP load testing tool)
# macOS: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Test search endpoint
hey -n 10 -c 1 -m POST \
  -H "Content-Type: application/json" \
  -d '{"query":"love","languages":["en"],"translations":["NIV"]}' \
  http://localhost:8000/api/search

# Expected:
# - Average response time: < 2 seconds (first query)
# - Cached queries: < 500ms
```

---

## Troubleshooting

### Common Issues

#### 1. Docker Services Won't Start

**Symptom:** `docker-compose up -d` fails

**Solutions:**
```bash
# Check if Docker is running
docker info

# Check port conflicts (5432, 6379)
lsof -i :5432  # macOS/Linux
netstat -ano | findstr :5432  # Windows

# If ports are in use, stop conflicting services or change ports in docker-compose.yml

# Reset Docker completely
docker-compose down -v
docker system prune -a  # WARNING: Removes all Docker data
docker-compose up -d
```

#### 2. Cannot Connect to PostgreSQL

**Symptom:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker exec -it bible-rag-postgres pg_isready -U bible_user

# Verify DATABASE_URL in backend/.env
cat backend/.env | grep DATABASE_URL

# Try connecting manually
docker exec -it bible-rag-postgres psql -U bible_user -d bible_rag
```

#### 3. pgvector Extension Error

**Symptom:** `ERROR: extension "vector" is not available`

**Solutions:**
```bash
# Connect to database
docker exec -it bible-rag-postgres psql -U bible_user -d bible_rag

# Install extension
CREATE EXTENSION vector;

# If error persists, check PostgreSQL version
SELECT version();
-- pgvector requires PostgreSQL 11+

# Rebuild Docker image with pgvector
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 4. Embedding Model Download Fails

**Symptom:** `OSError: Can't load model 'intfloat/multilingual-e5-large'`

**Solutions:**
```bash
# Check internet connection
ping huggingface.co

# Set HuggingFace cache directory (if disk space issues)
export HF_HOME=/path/to/large/disk/huggingface_cache
python embeddings.py

# Download model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')"

# Use alternative mirror (China)
export HF_ENDPOINT=https://hf-mirror.com
python embeddings.py
```

#### 5. Out of Memory During Embedding

**Symptom:** `Killed` or `MemoryError` during embedding generation

**Solutions:**
```bash
# Reduce batch size in embeddings.py
# Edit embeddings.py and change:
batch_size = 32  # Reduce to 16 or 8

# Monitor memory usage
# macOS:
vm_stat | grep "Pages free"

# Linux:
free -h

# Close other applications to free memory

# If still failing, generate embeddings in chunks
python embeddings.py --start-index 0 --end-index 10000
python embeddings.py --start-index 10000 --end-index 20000
# etc.
```

#### 6. Frontend Won't Start

**Symptom:** `npm run dev` fails

**Solutions:**
```bash
# Clear Next.js cache
rm -rf frontend/.next
rm -rf frontend/node_modules

# Reinstall dependencies
cd frontend
npm install

# Check for port conflicts (3000)
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Run on different port
npm run dev -- -p 3001

# Check Node.js version
node --version  # Should be 18+
```

#### 7. Korean Text Not Displaying

**Symptom:** Korean characters show as boxes or gibberish

**Solutions:**
```bash
# Verify font installation
# In browser DevTools > Network, check for Noto Sans KR font loading

# Clear Next.js cache and rebuild
rm -rf frontend/.next
npm run dev

# Check font configuration in tailwind.config.js
# Ensure Korean fonts are in fontFamily

# Test with browser DevTools > Elements
# Check computed font-family includes Korean fonts
```

#### 8. API Rate Limit Errors

**Symptom:** `429 Too Many Requests` from Gemini/Groq

**Solutions:**
```bash
# Check API key validity
curl -H "Authorization: Bearer $GEMINI_API_KEY" https://generativelanguage.googleapis.com/v1beta/models

# Verify rate limits in code
# backend/search.py should have fallback to Groq

# Test with reduced query rate
# Add delays between requests

# Use local LLM as fallback (Ollama)
# Install: curl -fsSL https://ollama.com/install.sh | sh
# Run: ollama pull llama3.2
# Update backend/.env: LOCAL_LLM_ENABLED=true
```

### Getting Help

**1. Check Logs:**
```bash
# Docker services
docker-compose logs

# Backend
# Should be visible in terminal running uvicorn

# Frontend
# Should be visible in terminal running npm run dev

# Database
docker exec -it bible-rag-postgres tail -f /var/log/postgresql/postgresql-*.log
```

**2. Enable Debug Mode:**

**Backend:**
```python
# In backend/main.py
app = FastAPI(debug=True)

# Or set environment variable
export DEBUG=1
uvicorn main:app --reload --log-level debug
```

**Frontend:**
```bash
# In frontend/.env.local
NEXT_PUBLIC_DEBUG=true

npm run dev
```

**3. Community Support:**
- GitHub Issues: https://github.com/yourusername/bible-rag/issues
- Documentation: See other docs/ files
- Email: your.email@example.com

---

## Next Steps

After successful setup:

1. **Read Architecture Documentation**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
2. **Explore API**: [docs/API.md](API.md)
3. **Learn Features**: [docs/FEATURES.md](FEATURES.md)
4. **Deploy to Production**: [docs/DEPLOYMENT.md](DEPLOYMENT.md)
