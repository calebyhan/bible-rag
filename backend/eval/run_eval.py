"""Evaluation harness for Bible RAG retrieval quality.

Runs the ground-truth query set (queries.json) against several retrieval
variants (BM25-only, semantic-only, hybrid RRF, hybrid RRF + reranker) and
reports precision@k, recall@k, MRR, and NDCG@k per category and overall,
plus per-variant latency.

Usage:
    python -m eval.run_eval [--k 10] [--out eval/results.json]
"""

import argparse
import asyncio
import json
import os
import sys
import time
from collections import defaultdict
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from database import AsyncSessionLocal
from eval.metrics import average_metrics, evaluate_query
from search import search_verses

settings = get_settings()

VARIANTS = {
    "bm25": {"enable_hybrid_search": True, "enable_reranking": False, "mock_vector": True, "expand": False},
    "semantic": {"enable_hybrid_search": False, "enable_reranking": False, "mock_vector": False, "expand": False},
    "hybrid_rrf": {"enable_hybrid_search": True, "enable_reranking": False, "mock_vector": False, "expand": False},
    "hybrid_rrf_rerank": {"enable_hybrid_search": True, "enable_reranking": True, "mock_vector": False, "expand": False},
    "hybrid_rrf_rerank_expansion": {"enable_hybrid_search": True, "enable_reranking": True, "mock_vector": False, "expand": True},
}


def ref_key(ref: dict) -> str:
    return f"{ref['book']}:{ref['chapter']}:{ref['verse']}"


def result_ref_key(result_item: dict) -> str:
    ref = result_item["reference"]
    return f"{ref['book_abbrev']}:{ref['chapter']}:{ref['verse']}"


async def run_variant(variant_name: str, variant_config: dict, queries: list[dict], translations: list[str], k: int):
    original_hybrid = settings.enable_hybrid_search
    original_rerank = settings.enable_reranking
    settings.enable_hybrid_search = variant_config["enable_hybrid_search"]
    settings.enable_reranking = variant_config["enable_reranking"]

    per_query_results = []
    try:
        async with AsyncSessionLocal() as db:
            for q in queries:
                relevant = {ref_key(r) for r in q["relevant"]}
                print(f"  [{variant_name}] {q['id']}...", flush=True)

                expanded_queries = None
                if variant_config["expand"]:
                    from llm import detect_language, expand_query
                    try:
                        expanded_queries = await asyncio.wait_for(
                            expand_query(query=q["query"], language=detect_language(q["query"])),
                            timeout=20,
                        )
                    except asyncio.TimeoutError:
                        print(f"    expand_query timed out for {q['id']}", flush=True)
                        expanded_queries = []

                start = time.time()
                if variant_config["mock_vector"]:
                    with patch("search._vector_search", new=AsyncMock(return_value=[])):
                        response = await search_verses(
                            db=db,
                            query=q["query"],
                            translations=translations,
                            max_results=k,
                            include_cross_refs=False,
                            include_original=False,
                            use_cache=False,
                            expanded_queries=expanded_queries,
                        )
                else:
                    response = await search_verses(
                        db=db,
                        query=q["query"],
                        translations=translations,
                        max_results=k,
                        include_cross_refs=False,
                        include_original=False,
                        use_cache=False,
                        expanded_queries=expanded_queries,
                    )
                elapsed_ms = (time.time() - start) * 1000

                retrieved = [result_ref_key(r) for r in response["results"]]
                metrics = evaluate_query(retrieved, relevant, k=k)

                per_query_results.append({
                    "id": q["id"],
                    "category": q["category"],
                    "query": q["query"],
                    "retrieved": retrieved,
                    "relevant": sorted(relevant),
                    "metrics": metrics,
                    "latency_ms": elapsed_ms,
                    "search_method": response["search_metadata"].get("search_method"),
                })
    finally:
        settings.enable_hybrid_search = original_hybrid
        settings.enable_reranking = original_rerank

    return per_query_results


def summarize(per_query_results: list[dict]) -> dict:
    overall = average_metrics([r["metrics"] for r in per_query_results])
    overall["avg_latency_ms"] = sum(r["latency_ms"] for r in per_query_results) / len(per_query_results)

    by_category = defaultdict(list)
    for r in per_query_results:
        by_category[r["category"]].append(r)

    category_summary = {}
    for cat, items in by_category.items():
        cat_metrics = average_metrics([r["metrics"] for r in items])
        cat_metrics["avg_latency_ms"] = sum(r["latency_ms"] for r in items) / len(items)
        category_summary[cat] = cat_metrics

    return {"overall": overall, "by_category": category_summary}


async def main(k: int, out_path: str, args_variants: list[str] | None = None):
    queries_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queries.json")
    with open(queries_path) as f:
        data = json.load(f)

    queries = data["queries"]
    translations = data["translations"]

    # Pre-warm models sequentially before any concurrent calls (mirrors main.py's
    # lifespan startup). Without this, asyncio.gather()-based concurrent embedding
    # calls during query expansion can race on the lazy-loading singletons in
    # embeddings.py/reranker.py and corrupt the model (PyTorch meta-tensor error).
    loop = asyncio.get_event_loop()
    if settings.embedding_mode == "local":
        print("Preloading embedding model...", flush=True)
        from embeddings import _get_local_model
        await loop.run_in_executor(None, _get_local_model)
    print("Preloading reranker...", flush=True)
    from reranker import _get_reranker
    await loop.run_in_executor(None, _get_reranker)

    import search as search_module
    search_module._has_embeddings = True

    all_results = {}
    if os.path.exists(out_path):
        with open(out_path) as f:
            all_results = json.load(f)

    variants_to_run = (
        {name: VARIANTS[name] for name in args_variants}
        if args_variants else VARIANTS
    )
    for variant_name, variant_config in variants_to_run.items():
        print(f"Running variant: {variant_name}...")
        per_query = await run_variant(variant_name, variant_config, queries, translations, k)
        summary = summarize(per_query)
        all_results[variant_name] = {"summary": summary, "per_query": per_query}
        print(f"  precision@{k}={summary['overall']['precision@k']:.3f}  "
              f"recall@{k}={summary['overall']['recall@k']:.3f}  "
              f"mrr={summary['overall']['mrr']:.3f}  "
              f"ndcg@{k}={summary['overall']['ndcg@k']:.3f}  "
              f"latency={summary['overall']['avg_latency_ms']:.0f}ms")

    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nFull results written to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json"))
    parser.add_argument("--variants", nargs="*", default=None, choices=list(VARIANTS.keys()))
    args = parser.parse_args()

    asyncio.run(main(args.k, args.out, args.variants))
