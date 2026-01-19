"""Unified embedding module supporting local model and Gemini API.

This module provides a flexible embedding system that can use either:
- Local sentence-transformers model (for development/self-hosted with 4GB+ RAM)
- Gemini API (for production on free tier hosts with limited RAM)

The mode is controlled by the EMBEDDING_MODE environment variable.
"""

import numpy as np

from config import get_settings

settings = get_settings()

# Local model (lazy loaded only when needed)
_local_model = None


def _get_local_model():
    """Load local sentence-transformers model (only in local mode).

    The model is loaded lazily on first use and cached for subsequent calls.
    This avoids loading the ~4GB model when using Gemini API mode.
    """
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        print(f"Loading local embedding model: {settings.embedding_model}")
        _local_model = SentenceTransformer(settings.embedding_model)
        print("Model loaded successfully!")
    return _local_model


def embed_query_local(query: str) -> np.ndarray:
    """Generate embedding using local sentence-transformers model.

    Args:
        query: Search query text

    Returns:
        1024-dimensional embedding vector
    """
    model = _get_local_model()
    embedding = model.encode(
        f"query: {query}",
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embedding


def embed_query_gemini(query: str, api_key: str) -> np.ndarray:
    """Generate embedding using Gemini API.

    Uses gemini-embedding-001 with output_dimensionality=1024 to match
    the local model's embeddings.

    Args:
        query: Search query text
        api_key: User's Gemini API key

    Returns:
        1024-dimensional embedding vector
    """
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=query,
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=1024,
    )
    return np.array(result["embedding"])


def embed_query(query: str, api_key: str | None = None) -> np.ndarray:
    """Generate query embedding using configured mode.

    The embedding mode is determined by EMBEDDING_MODE environment variable:
    - "local": Uses sentence-transformers (requires 4GB+ RAM)
    - "gemini": Uses Gemini API (requires API key, works on free tier hosts)

    Args:
        query: Search query text
        api_key: Gemini API key (required if EMBEDDING_MODE=gemini)

    Returns:
        1024-dimensional embedding vector

    Raises:
        ValueError: If gemini mode but no API key provided
    """
    if settings.embedding_mode == "gemini":
        if not api_key:
            raise ValueError(
                "Gemini API key required for embedding (EMBEDDING_MODE=gemini). "
                "Please provide your API key in the settings."
            )
        return embed_query_gemini(query, api_key)
    else:
        return embed_query_local(query)


def embed_texts(texts: list[str], api_key: str | None = None) -> np.ndarray:
    """Generate embeddings for multiple texts (for batch operations).

    Args:
        texts: List of texts to embed
        api_key: Gemini API key (required if EMBEDDING_MODE=gemini)

    Returns:
        Array of shape (len(texts), 1024)
    """
    if settings.embedding_mode == "gemini":
        if not api_key:
            raise ValueError("Gemini API key required for embedding")
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=1024,
            )
            embeddings.append(result["embedding"])
        return np.array(embeddings)
    else:
        model = _get_local_model()
        prefixed = [f"passage: {t}" for t in texts]
        return model.encode(prefixed, normalize_embeddings=True)
