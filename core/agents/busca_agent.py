from __future__ import annotations
from typing import Any, Dict, List, Optional
import time
from pathlib import Path

from core.rag.faiss_search import FaissSearcher
from core.utils.logging import get_logger


_INDEX_DIR = Path("data/indexes/cdc_faiss")
_TOP_K_DEFAULT = 5
_MAX_RESULTS_FOR_REDATOR = 5

logger = get_logger(__name__)


def _get_searcher() -> Optional[FaissSearcher]:
    """Initialize FAISS searcher if index exists."""
    if FaissSearcher is None:
        return None
    index_file = _INDEX_DIR / "cdc.index"
    if not index_file.exists():
        return None
    try:
        return FaissSearcher(_INDEX_DIR)
    except Exception:
        return None


_SEARCHER = _get_searcher()


def _normalize_query(text: str) -> str:
    """Lowercase + collapse whitespace for logging/analytics."""
    return " ".join(text.lower().split())


def _dedupe_results(results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Deduplicate results by artigo/id keeping original order."""
    seen: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for item in results:
        key = str(item.get("artigo") or item.get("id") or "")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Busca agent: RAG retrieval from FAISS index.

    Short-circuits if triagem blocked the query.
    """
    # Short-circuit if triagem blocked
    if state.get("blocks", {}).get("error"):
        return state

    start_ts = time.time()
    k = int(state.get("k") or _TOP_K_DEFAULT)
    k = max(1, min(k, _MAX_RESULTS_FOR_REDATOR))
    results: List[Dict[str, Any]] = []
    query = state.get("cleaned_query", "")
    normalized_query = _normalize_query(query) if query else ""

    if _SEARCHER is not None and query:
        try:
            logger.info("BuscaAgent: searching top-%d for query: %s", k, query[:80])
            raw_results = _SEARCHER.search(query, k=k * 2)
            results = _dedupe_results(raw_results, limit=k)
        except Exception:
            results = []

    # Log detailed hits with scores
    if results:
        for idx, r in enumerate(results, start=1):
            rid = r.get("id") or r.get("artigo") or f"hit-{idx}"
            score = r.get("score")
            artigo = r.get("artigo") or ""
            logger.info(
                "BuscaAgent hit#%d score=%s id=%s artigo=%s",
                idx,
                str(score),
                str(rid),
                str(artigo),
            )

    elapsed_ms = int((time.time() - start_ts) * 1000)
    meta = dict(state.get("meta", {}))
    meta["busca"] = {
        "k": k,
        "hits": len(results),
        "query_original": query,
        "query_normalized": normalized_query,
        "ids": [r.get("id") for r in results if r.get("id")],
        "scores": [r.get("score") for r in results],
        "elapsed_ms": elapsed_ms,
    }
    state.update({"sources": results, "meta": meta})
    logger.info("BuscaAgent: hits=%d elapsed=%dms", len(results), elapsed_ms)
    return state
