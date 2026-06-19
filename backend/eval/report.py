"""Generate a markdown comparison report from eval/results.json.

Usage:
    python -m eval.report [--results eval/results.json] [--out eval/REPORT.md]
"""

import argparse
import json
import os

VARIANT_LABELS = {
    "bm25": "BM25 (full-text only)",
    "semantic": "Semantic (vector only)",
    "hybrid_rrf": "Hybrid RRF (vector + BM25)",
    "hybrid_rrf_rerank": "Hybrid RRF + Reranker",
    "hybrid_rrf_rerank_expansion": "Hybrid RRF + Reranker + Query Expansion",
}

METRIC_LABELS = {
    "precision@k": "Precision@10",
    "recall@k": "Recall@10",
    "mrr": "MRR",
    "ndcg@k": "NDCG@10",
    "avg_latency_ms": "Avg Latency (ms)",
}


def fmt(value: float, is_latency: bool = False) -> str:
    if is_latency:
        return f"{value:.0f}"
    return f"{value:.3f}"


METHODOLOGY = """
## Research Question

Does hybrid retrieval (BM25 + dense embeddings, fused with RRF) and cross-encoder
reranking improve retrieval quality over single-method baselines for a
multilingual (English/Korean) Bible search system — and does that benefit hold
for cross-lingual queries?

## Methodology

- **Query set**: 40 hand-written queries across 4 categories (10 each):
  `thematic` (theological topics, e.g. "What does the Bible say about hope?"),
  `narrative` (Bible stories, e.g. "David and Goliath"), `korean` (the same
  style of queries written in Korean), and `cross_lingual` (Korean queries
  about English-labeled concepts, or English queries containing Korean terms).
- **Ground truth**: each query is labeled with a small set (3-8) of
  `(book, chapter, verse)` references representing the canonical/most relevant
  verses, identified manually from theological knowledge. Relevance is binary
  and verse-level (translation-independent), so this rewards precise retrieval
  of the *exact* verses scholars would point to, not just topically-adjacent
  passages.
- **Retrieval variants** (toggled via `config.Settings` flags, called directly
  through `search.search_verses()` to bypass the streaming API):
  - `bm25`: PostgreSQL full-text search only (`_vector_search` mocked to
    return nothing).
  - `semantic`: dense vector search only (`enable_hybrid_search=False`).
  - `hybrid_rrf`: vector + BM25 fused via weighted Reciprocal Rank Fusion,
    no reranking.
  - `hybrid_rrf_rerank`: the above + `BAAI/bge-reranker-v2-m3` cross-encoder
    reranking of the top 30 candidates (this is the system's default
    production configuration).
  - `hybrid_rrf_rerank_expansion`: the above + LLM-based query expansion
    (`enable_query_expansion`) — the original query plus 3 LLM-generated
    alternative phrasings are embedded and searched in parallel, then fused
    via weighted RRF (main query weight=2.0, expansions weight=1.0) before
    reranking.
- **Metrics**: Precision@10, Recall@10, MRR, NDCG@10, averaged per query and
  per category. Latency is wall-clock time for `search_verses()` per query
  (cache disabled).

"""

INSIGHTS = """
## Key Insights

1. **BM25 cannot retrieve Korean text at all.** Across all 10 `korean` and 10
   `cross_lingual` queries, the full-text-only variant returned **zero**
   results (`search_method: "none"`) for every Korean-language query. The
   full-text search uses `to_tsvector('english', ...)`, which doesn't
   tokenize Hangul — Korean verses are invisible to BM25 entirely. This is the
   single biggest correctness gap in the retrieval stack for the project's
   stated "Korean UX" priority.

2. **Reranking is the largest lever on retrieval quality**, improving overall
   NDCG@10 from 0.147 (hybrid RRF) to 0.185 (+26%) and recall@10 from 0.153 to
   0.198 (+29%) — but at roughly **2.8x the latency** (950ms -> 2635ms). The
   gain is concentrated in `narrative` (NDCG 0.228 -> 0.303) and
   `cross_lingual` (0.087 -> 0.197) categories.

3. **Reranking can hurt thematic queries.** For the `thematic` category,
   precision@10 *drops* slightly with reranking (0.058 -> 0.050) and recall is
   flat. Thematic queries (e.g. "What does the Bible say about hope?") have
   many topically-adjacent but non-canonical matches; the cross-encoder, which
   is tuned for semantic relevance to the query string, doesn't reliably
   prefer the small set of "classic" verses a human would cite over equally
   relevant-sounding alternatives.

4. **Hybrid RRF rarely beats semantic-only before reranking.** In the
   `narrative` and `cross_lingual` categories, `hybrid_rrf` produces *identical*
   precision/recall to `semantic` alone — BM25 contributes few or no candidates
   to the fused list for these queries (especially Korean, per #1), so RRF
   fusion is a no-op. The hybrid step earns its keep mainly as a feeder to the
   reranker, not as a ranking signal on its own.

5. **Korean queries retrieve relevant verses via embeddings but rarely in the
   top 10.** Semantic search achieves MRR 0.245-0.333 on Korean queries
   (the first hit is often relevant), but precision@10/recall@10 stay low
   (0.04-0.05 / 0.12-0.14) — the multilingual embedding model finds *a*
   relevant verse but doesn't densely cluster all the canonically relevant
   verses near the top, unlike English narrative queries (precision@10 0.138).

6. **Latency**: BM25-only is by far the fastest (~170-865ms, dominated by the
   embedding call that always runs regardless of variant). Reranking adds
   ~1.3-2.3s per query on CPU. For a production system, this is the key
   quality/latency tradeoff: the default `hybrid_rrf_rerank` configuration
   roughly doubles best-case latency for a ~25% NDCG improvement.

7. **Query expansion gives marginal quality gains for a 3x latency cost.**
   Adding LLM-based query expansion on top of `hybrid_rrf_rerank` improves
   overall NDCG@10 from 0.185 to 0.192 (+4%), recall@10 from 0.198 to 0.210
   (+6%), and MRR from 0.310 to 0.315 (+1.5%) — but average latency jumps from
   2635ms to 8215ms (+212%), since the original query plus all 3 LLM-generated
   alternatives are each embedded, searched, and fused before reranking. The
   gains are concentrated in `narrative` (NDCG 0.303 -> 0.318, precision@10
   0.188 -> 0.200) and `cross_lingual` (NDCG 0.197 -> 0.211, recall@10 0.227
   -> 0.260). For `thematic` and `korean` queries, expansion is essentially a
   wash (NDCG@10 0.135 -> 0.138 and 0.138 -> 0.137 respectively) — for Korean,
   this tracks with #1 and #5: expansion can't fix BM25's inability to index
   Hangul, and the embedding model already finds the relevant verse via
   semantic search alone.

8. **Concurrent first-time model loading can silently corrupt the embedding
   and reranker models.** While building this harness, running query
   expansion's `asyncio.gather()`-based concurrent embedding calls *before*
   either model had been loaded triggered a PyTorch
   `"Cannot copy out of meta tensor"` error: two coroutines both saw
   `_local_model is None` (the lazy singleton in `embeddings.py`) and started
   loading the model concurrently, corrupting it for the rest of the process
   (and the reranker similarly, via `reranker.py`). Production is currently
   protected because `main.py`'s `lifespan()` pre-warms both models
   *sequentially* at startup before any request can trigger a concurrent load
   — but this makes the lazy-singleton pattern a latent footgun for any other
   code path (e.g. a future worker process, a test harness, or a startup
   change that defers warm-up) that calls these loaders concurrently before
   warm-up completes. See Recommendations.

## Limitations

- **Ground truth is small and verse-level.** 40 queries with 3-8 labeled
  verses each is enough to see clear directional differences but not enough
  for tight confidence intervals. Verse-level (vs. chapter-level) relevance is
  a deliberately strict bar — it rewards finding the *exact* verses a person
  would cite, which penalizes systems that retrieve "close" verses (e.g. the
  surrounding narrative).
- **Single embedding model.** All variants use `intfloat/multilingual-e5-large`;
  no smaller-model ablation was run.
- **Query expansion latency is environment-dependent.** The 8.2s average for
  `hybrid_rrf_rerank_expansion` includes 1-3 sequential LLM calls (Groq with
  Gemini fallback) per query; this varies with provider latency/rate limits
  and would differ in production where requests are spread out rather than
  run back-to-back in a 40-query batch.

## Recommendations

1. **Fix Korean full-text search** — use a Korean-aware text search
   configuration (e.g. PostgreSQL's `simple` config with a Korean
   tokenizer/dictionary, or a separate `pg_bigm`/trigram index) so BM25 can
   contribute to RRF for Korean queries. This is the highest-impact fix given
   the project's Korean-first audience.
2. **Consider a precision-oriented mode for thematic queries** — e.g. skip
   reranking (or down-weight it) when the query is classified as thematic,
   since reranking measurably hurts precision there.
3. **Make reranking latency-aware** — e.g. only rerank when `max_results` is
   small, or rerank a smaller top-N for thematic queries, to recover some of
   the ~1.5s latency cost without losing the narrative/cross-lingual gains.
4. **Reconsider when query expansion is worth it.** Given a +4% NDCG gain for
   +212% latency, query expansion should likely be opt-in (e.g. an "advanced
   search" toggle, or applied only to `narrative`/`cross_lingual` queries
   where it helps most) rather than always-on, especially for a chat-style UI
   where response latency directly affects perceived quality.
5. **Add a lock around the lazy model-loading singletons** — wrap
   `_get_local_model()` in `embeddings.py` and `_get_reranker()` in
   `reranker.py` with a `threading.Lock()` so concurrent first-time calls
   block on the same load instead of racing. This is defense-in-depth: the
   current `lifespan()` warm-up avoids the issue in normal production
   operation, but a lock makes the singletons correct on their own merits.
"""


def build_report(results: dict) -> str:
    lines = []
    lines.append("# Bible RAG Retrieval Evaluation Report\n")
    lines.append(METHODOLOGY)

    # Overall comparison table
    lines.append("## Overall Comparison\n")
    metric_keys = ["precision@k", "recall@k", "mrr", "ndcg@k", "avg_latency_ms"]
    header = ["Variant"] + [METRIC_LABELS[m] for m in metric_keys]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for variant, data in results.items():
        overall = data["summary"]["overall"]
        row = [VARIANT_LABELS.get(variant, variant)]
        for m in metric_keys:
            row.append(fmt(overall[m], is_latency=(m == "avg_latency_ms")))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # Per-category breakdown
    categories = set()
    for data in results.values():
        categories.update(data["summary"]["by_category"].keys())

    for category in sorted(categories):
        lines.append(f"## Category: {category}\n")
        header = ["Variant"] + [METRIC_LABELS[m] for m in metric_keys]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))
        for variant, data in results.items():
            cat_data = data["summary"]["by_category"].get(category)
            if not cat_data:
                continue
            row = [VARIANT_LABELS.get(variant, variant)]
            for m in metric_keys:
                row.append(fmt(cat_data[m], is_latency=(m == "avg_latency_ms")))
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    lines.append(INSIGHTS)

    return "\n".join(lines)


def main(results_path: str, out_path: str):
    with open(results_path) as f:
        results = json.load(f)

    report = build_report(results)
    with open(out_path, "w") as f:
        f.write(report)
    print(f"Report written to {out_path}")
    print()
    print(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--results", default=os.path.join(base, "results.json"))
    parser.add_argument("--out", default=os.path.join(base, "REPORT.md"))
    args = parser.parse_args()

    main(args.results, args.out)
