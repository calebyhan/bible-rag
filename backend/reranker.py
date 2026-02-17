"""Cross-encoder reranking for improved search precision.

Uses a multilingual cross-encoder model to jointly score (query, passage)
pairs, providing fine-grained relevance scoring after initial retrieval.
"""

import logging

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_reranker = None


def _get_reranker():
    """Load cross-encoder model (lazy, cached singleton)."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder

        logger.info(f"Loading reranker model: {settings.reranker_model}")
        _reranker = CrossEncoder(settings.reranker_model, max_length=512)
        logger.info("Reranker model loaded successfully")
    return _reranker


def rerank(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    """Rerank candidates using cross-encoder.

    Args:
        query: Search query
        candidates: List of dicts with at minimum a "text" field
        top_k: Number of results to return

    Returns:
        Top-k candidates reordered by cross-encoder score
    """
    if not candidates:
        return candidates

    reranker = _get_reranker()
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker.predict(pairs)

    for i, c in enumerate(candidates):
        c["rerank_score"] = float(scores[i])

    return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)[:top_k]
