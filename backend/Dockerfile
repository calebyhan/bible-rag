# Multi-stage build for production deployment
FROM python:3.10-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies (exclude heavy ML dependencies for Gemini API mode)
RUN pip install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn[standard]==0.34.0 \
    python-multipart==0.0.18 \
    sqlalchemy==2.0.36 \
    psycopg2-binary==2.9.10 \
    pgvector==0.3.6 \
    alembic==1.14.0 \
    redis==5.2.1 \
    google-generativeai==0.8.3 \
    groq==0.14.0 \
    pydantic==2.10.4 \
    pydantic-settings==2.7.0 \
    python-dotenv==1.0.1 \
    httpx==0.28.1 \
    tqdm==4.67.1 \
    unicodedata2==15.1.0

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
