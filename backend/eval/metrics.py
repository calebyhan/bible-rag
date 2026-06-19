"""Retrieval evaluation metrics: precision@k, recall@k, MRR, NDCG@k."""

import math


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the top-k retrieved items that are relevant."""
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for ref in top_k if ref in relevant)
    return hits / len(top_k)


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant items found within the top-k retrieved items."""
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    hits = sum(1 for ref in top_k if ref in relevant)
    return hits / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """1 / rank of the first relevant item, or 0 if none found."""
    for i, ref in enumerate(retrieved, start=1):
        if ref in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Normalized discounted cumulative gain at k (binary relevance)."""
    top_k = retrieved[:k]
    dcg = sum(
        1.0 / math.log2(i + 1)
        for i, ref in enumerate(top_k, start=1)
        if ref in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def evaluate_query(retrieved: list[str], relevant: set[str], k: int = 10) -> dict:
    """Compute all metrics for a single query at the given cutoff k."""
    return {
        "precision@k": precision_at_k(retrieved, relevant, k),
        "recall@k": recall_at_k(retrieved, relevant, k),
        "mrr": reciprocal_rank(retrieved, relevant),
        "ndcg@k": ndcg_at_k(retrieved, relevant, k),
    }


def average_metrics(per_query_metrics: list[dict]) -> dict:
    """Average a list of per-query metric dicts."""
    if not per_query_metrics:
        return {"precision@k": 0.0, "recall@k": 0.0, "mrr": 0.0, "ndcg@k": 0.0}
    keys = per_query_metrics[0].keys()
    return {
        key: sum(m[key] for m in per_query_metrics) / len(per_query_metrics)
        for key in keys
    }
