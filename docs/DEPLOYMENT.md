# Bible RAG - Deployment Guide

Complete guide for deploying the Bible RAG system to production.

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Prerequisites](#prerequisites)
- [Database Deployment (Supabase)](#database-deployment-supabase)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Redis Deployment (Upstash)](#redis-deployment-upstash)
- [Environment Variables](#environment-variables)
- [DNS & Domain Setup](#dns--domain-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Performance Tuning](#performance-tuning)
- [Rollback Procedures](#rollback-procedures)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Deployment Overview

### Production Architecture

```mermaid
graph TB
    CDN["CloudFlare CDN<br/>(DNS + DDoS Protection)"]
    
    subgraph Vercel["Frontend (Vercel)"]
        Frontend["Next.js 16<br/>- Global CDN<br/>- Edge functions<br/>- Auto HTTPS"]
    end
    
    subgraph Railway["Backend (Railway)"]
        Backend["FastAPI<br/>- Auto-scaling<br/>- Health checks<br/>- Log aggregation"]
    end
    
    subgraph Supabase["Supabase"]
        DB["PostgreSQL<br/>+ pgvector<br/>- Backups<br/>- Monitoring"]
    end
    
    subgraph Upstash["Upstash"]
        Cache["Redis<br/>- Cache<br/>- Sessions"]
    end
    
    subgraph External["External APIs"]
        APIs["- Gemini<br/>- Groq"]
    end
    
    CDN --> Vercel
    CDN --> Railway
    Frontend -.->|API Calls| Backend
    Backend --> Supabase
    Backend --> Upstash
    Backend --> External
```

### Deployment Stages

1. **Local Development** → Fully local (Docker Compose)
2. **Staging** → Cloud services, test data
3. **Production** → Cloud services, full data, monitoring

---

## Prerequisites

### Accounts Needed

1. **Supabase** (Database)
   - Sign up: https://supabase.com
   - Free tier: 500MB database, unlimited API requests

2. **Vercel** (Frontend + Backend option)
   - Sign up: https://vercel.com
   - Free tier: 100GB bandwidth/month

3. **Railway** (Backend alternative)
   - Sign up: https://railway.app
   - Free tier: $5 credit/month

4. **Upstash** (Redis)
   - Sign up: https://upstash.com
   - Free tier: 10K commands/day

5. **CloudFlare** (Optional - DNS)
   - Sign up: https://cloudflare.com
   - Free tier: DDoS protection, CDN

### Tools Required

```bash
# Install required CLI tools
npm install -g vercel        # Vercel CLI
brew install supabase/tap/supabase  # Supabase CLI
```

---

## Database Deployment (Supabase)

### Step 1: Create Supabase Project

1. **Create Project:**
   - Go to https://app.supabase.com
   - Click "New Project"
   - Name: `bible-rag-prod`
   - Region: Choose closest to users (e.g., `us-west-1` for US/Korea)
   - Database password: Generate strong password
   - Click "Create new project" (takes ~2 minutes)

2. **Note Connection Details:**
   ```
   Project URL: https://abcdefgh.supabase.co
   API Key (anon): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Database URL: postgresql://postgres:[password]@db.abcdefgh.supabase.co:5432/postgres
   ```

### Step 2: Enable pgvector Extension

1. Go to **Database** → **Extensions**
2. Search for `vector`
3. Click "Enable" on `vector` extension
4. Verify in SQL Editor:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

### Step 3: Create Schema

1. Go to **SQL Editor**
2. Create new query
3. Paste schema from `docs/DATABASE.md`
4. Run query

**Or use Supabase CLI:**
```bash
# Login
supabase login

# Link project
supabase link --project-ref abcdefgh

# Run migrations
supabase db push
```

### Step 4: Migrate Data

**From Local PostgreSQL:**

```bash
# Export from local
pg_dump -h localhost -U bible_user -d bible_rag \
    --no-owner --no-privileges \
    -f bible_rag_export.sql

# Import to Supabase
psql -h db.abcdefgh.supabase.co \
    -U postgres -d postgres \
    -f bible_rag_export.sql
```

**Using Python Script:**

```python
# migrate_to_supabase.py
import psycopg2
from tqdm import tqdm
import os

LOCAL_DB = os.getenv('LOCAL_DATABASE_URL')
SUPABASE_DB = os.getenv('SUPABASE_DATABASE_URL')

def migrate():
    local_conn = psycopg2.connect(LOCAL_DB)
    supabase_conn = psycopg2.connect(SUPABASE_DB)

    tables = ['translations', 'books', 'verses', 'embeddings',
              'cross_references', 'original_words']

    for table in tables:
        print(f"Migrating {table}...")
        local_cur = local_conn.cursor()
        supabase_cur = supabase_conn.cursor()

        # Fetch all data
        local_cur.execute(f"SELECT * FROM {table}")
        rows = local_cur.fetchall()
        columns = [desc[0] for desc in local_cur.description]

        # Insert to Supabase
        placeholders = ','.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"

        for row in tqdm(rows, desc=table):
            supabase_cur.execute(insert_sql, row)

        supabase_conn.commit()
        print(f"✓ Migrated {len(rows)} rows")

    local_conn.close()
    supabase_conn.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate()
```

Run migration:
```bash
python scripts/migrate_to_supabase.py
```

### Step 5: Create Indexes

```sql
-- In Supabase SQL Editor
-- Create vector index (takes 5-10 minutes for 31K vectors)
CREATE INDEX idx_embeddings_vector ON embeddings
    USING ivfflat (vector vector_cosine_ops)
    WITH (lists = 100);

-- Analyze for query optimization
ANALYZE verses;
ANALYZE embeddings;
```

### Step 6: Configure Row Level Security (RLS)

```sql
-- Enable RLS (optional for read-only API)
ALTER TABLE verses ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Public read access" ON verses
    FOR SELECT USING (true);

CREATE POLICY "Public read access" ON embeddings
    FOR SELECT USING (true);
```

---

## Backend Deployment

### Option A: Deploy to Railway

#### Step 1: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Connect your `bible-rag` repository
4. Select `backend` directory as root

#### Step 2: Configure Build

Create `railway.toml` in project root:

```toml
[build]
builder = "nixpacks"
buildCommand = "cd backend && pip install -r requirements.txt"

[deploy]
startCommand = "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

#### Step 3: Set Environment Variables

In Railway dashboard → Variables:

```bash
DATABASE_URL=postgresql://postgres:[password]@db.abcdefgh.supabase.co:5432/postgres
REDIS_URL=redis://default:[password]@redis-12345.upstash.io:6379
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
EMBEDDING_MODEL=intfloat/multilingual-e5-large
PYTHON_VERSION=3.14
```

#### Step 4: Deploy

```bash
# Railway will auto-deploy on git push
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### Option B: Deploy to Vercel (Serverless)

#### Step 1: Create `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "backend/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/main.py"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.14"
  }
}
```

#### Step 2: Deploy

```bash
cd backend
vercel --prod

# Follow prompts:
# - Link to existing project or create new
# - Set environment variables
```

### Health Check Endpoint

Ensure `/health` endpoint is accessible:

```bash
curl https://your-backend.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "embedding_model": "loaded"
  }
}
```

---

## Frontend Deployment (Vercel)

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Configure Next.js for Production

**`frontend/next.config.js`:**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compress: true,

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Korean font optimization
  optimizeFonts: true,

  // Image optimization
  images: {
    domains: [],
    formats: ['image/avif', 'image/webp'],
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

### Step 3: Deploy to Vercel

```bash
cd frontend

# Login to Vercel
vercel login

# Deploy to production
vercel --prod

# Follow prompts:
# Project name: bible-rag-frontend
# Framework: Next.js
# Build command: npm run build
# Output directory: .next
```

### Step 4: Set Environment Variables

In Vercel Dashboard → Settings → Environment Variables:

```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_APP_NAME=Bible RAG
```

### Step 5: Configure Custom Domain (Optional)

1. Go to Vercel Dashboard → Domains
2. Add custom domain: `bible-rag.com`
3. Update DNS records as instructed
4. Wait for SSL certificate (automatic)

---

## Redis Deployment (Upstash)

### Step 1: Create Upstash Database

1. Go to https://console.upstash.com/redis
2. Click "Create Database"
3. Name: `bible-rag-cache`
4. Region: Choose closest to backend
5. Type: Regional (free tier)
6. Click "Create"

### Step 2: Get Connection Details

Copy Redis URL:
```
redis://default:[password]@redis-12345.upstash.io:6379
```

### Step 3: Test Connection

```bash
redis-cli -u redis://default:[password]@redis-12345.upstash.io:6379

# Test commands
> PING
PONG
> SET test "Hello"
OK
> GET test
"Hello"
```

### Step 4: Configure in Backend

Update backend environment variables:
```bash
REDIS_URL=redis://default:[password]@redis-12345.upstash.io:6379
CACHE_TTL=86400
```

---

## Environment Variables

### Complete Environment Variable List

#### Backend

Create `.env.production`:

```bash
# Database
DATABASE_URL=postgresql://postgres:[password]@db.abcdefgh.supabase.co:5432/postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[your-password]
POSTGRES_DB=postgres

# Redis
REDIS_URL=redis://default:[password]@redis-12345.upstash.io:6379

# API Keys
GEMINI_API_KEY=[your-gemini-key]
GROQ_API_KEY=[your-groq-key]

# Embedding Model
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DIMENSION=1024

# Cache Settings
CACHE_TTL=86400  # 24 hours

# Search Settings
MAX_RESULTS_DEFAULT=10
VECTOR_SEARCH_LISTS=100

# CORS
ALLOWED_ORIGINS=https://bible-rag.vercel.app,https://bible-rag.com

# Environment
ENVIRONMENT=production
DEBUG=false
```

#### Frontend

Create `.env.production`:

```bash
NEXT_PUBLIC_API_URL=https://bible-rag-api.railway.app
NEXT_PUBLIC_APP_NAME=Bible RAG
NEXT_PUBLIC_DEFAULT_LANGUAGE=en
NEXT_PUBLIC_SUPPORTED_LANGUAGES=en,ko
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

---

## DNS & Domain Setup

### Step 1: Purchase Domain

Options:
- Namecheap: https://namecheap.com
- Google Domains: https://domains.google
- CloudFlare Registrar: https://cloudflare.com

### Step 2: Configure DNS (CloudFlare)

1. Add domain to CloudFlare
2. Update nameservers at registrar
3. Add DNS records:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | @ | Vercel IP | Yes |
| CNAME | www | bible-rag.vercel.app | Yes |
| CNAME | api | bible-rag-api.railway.app | Yes |

### Step 3: SSL Certificate

- CloudFlare: Automatic (Free)
- Vercel: Automatic (Free)
- Railway: Automatic (Free)

---

## Monitoring & Logging

### Supabase Monitoring

1. Go to Supabase Dashboard → Database → Logs
2. Enable slow query logging:
   ```sql
   ALTER DATABASE postgres SET log_min_duration_statement = 1000;  -- Log queries > 1s
   ```

### Vercel Analytics

1. Go to Vercel Dashboard → Analytics
2. Enable Web Analytics (free)
3. View metrics: Page views, performance, errors

### Railway Logging

1. Go to Railway Dashboard → Your Service → Logs
2. View real-time logs
3. Filter by error level

### Custom Monitoring (BetterStack)

```bash
# Add logging middleware to FastAPI
from better_stack import logger

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info({
        "path": request.url.path,
        "method": request.method,
        "status": response.status_code,
        "duration_ms": ...
    })
    return response
```

### Health Check Monitoring

Use Uptime Robot (free):
1. Sign up: https://uptimerobot.com
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-backend.railway.app/health`
   - Interval: 5 minutes
3. Set up alerts (email, Slack, etc.)

---

## Performance Tuning

### Database Optimization

```sql
-- Connection pooling (Supabase auto-configured)
-- Max connections: 100 (Free tier)

-- Vacuum and analyze regularly
VACUUM ANALYZE;

-- Update statistics
ANALYZE verses;
ANALYZE embeddings;

-- Check slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Backend Optimization

**Gunicorn with Multiple Workers (Railway):**

```python
# backend/gunicorn_conf.py
workers = 4  # CPU cores
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
keepalive = 120
timeout = 120
```

**Update `railway.toml`:**
```toml
[deploy]
startCommand = "cd backend && gunicorn main:app -c gunicorn_conf.py"
```

### Frontend Optimization

**Enable Turbopack (Next.js 16):**
```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start"
  }
}
```

**Image Optimization:**
```typescript
import Image from 'next/image'

<Image
  src="/logo.png"
  width={200}
  height={200}
  alt="Logo"
  priority  // For above-the-fold images
/>
```

### CDN Configuration

**CloudFlare Caching:**
1. Go to CloudFlare → Caching → Configuration
2. Browser Cache TTL: 4 hours
3. Caching Level: Standard
4. Enable Auto Minify (HTML, CSS, JS)

---

## Rollback Procedures

### Database Rollback

```bash
# Restore from Supabase backup
supabase db restore --restore-id [backup-id]

# Or manual restore
pg_restore -h db.abcdefgh.supabase.co \
    -U postgres -d postgres \
    -c backup_20260111.dump
```

### Backend Rollback

**Railway:**
1. Go to Dashboard → Deployments
2. Click on previous working deployment
3. Click "Redeploy"

**Vercel:**
```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback [deployment-url]
```

### Frontend Rollback

**Vercel:**
1. Go to Dashboard → Deployments
2. Click on previous deployment
3. Click "Promote to Production"

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v

  deploy-backend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway
        run: |
          # Railway auto-deploys on push
          echo "Backend deployed to Railway"

  deploy-frontend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID}}
          vercel-args: '--prod'
          working-directory: ./frontend
```

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Embeddings uploaded to Supabase
- [ ] Health check endpoint responding
- [ ] Monitoring alerts configured
- [ ] Backup strategy in place
- [ ] SSL certificates valid
- [ ] DNS records configured
- [ ] Rate limiting enabled
