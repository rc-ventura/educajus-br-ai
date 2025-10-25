from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.rag.faiss_search import FaissSearcher
from core.utils.logging import get_logger


_INDEX_DIR = Path("data/indexes/cdc_faiss")
_TOP_K_DEFAULT = 5

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


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Busca agent: RAG retrieval from FAISS index.
    
    Short-circuits if triagem blocked the query.
    """
    # Short-circuit if triagem blocked
    if state.get("blocks", {}).get("error"):
        return state

    k = int(state.get("k") or _TOP_K_DEFAULT)
    k = max(1, min(k, 10))
    results: List[Dict[str, Any]] = []

    if _SEARCHER is not None and state.get("cleaned_query"):
        try:
            query = state["cleaned_query"]
            logger.info("BuscaAgent: searching top-%d for query: %s", k, query[:80])
            results = _SEARCHER.search(query, k=k)
        except Exception:
            results = []

    meta = dict(state.get("meta", {}))
    meta["busca"] = {"k": k, "hits": len(results)}
    state.update({"sources": results, "meta": meta})
    logger.info("BuscaAgent: hits=%d", len(results))
    return state
