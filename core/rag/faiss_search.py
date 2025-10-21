from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json
import numpy as np
import faiss  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore


class FaissSearcher:
    def __init__(self, index_dir: str | Path):
        self.index_dir = Path(index_dir)
        self.index = faiss.read_index(str(self.index_dir / "cdc.index"))

        with (self.index_dir / "cdc_metadata.json").open("r", encoding="utf-8") as f:
            md = json.load(f)

        self.model_name: str = md["model"]
        self.meta: List[Dict[str, Any]] = md["meta"]
        self.model = SentenceTransformer(self.model_name)

        # Safety: ensure metadata aligns with positional FAISS index
        ntotal = getattr(self.index, "ntotal", None)
        if ntotal is not None and ntotal != len(self.meta):
            raise ValueError(
                f"Metadata/index mismatch: index.ntotal={ntotal} vs len(meta)={len(self.meta)}. "
                "Rebuild either the index or the metadata to match the same order."
            )

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        # Guard against empty input
        if not query or not query.strip():
            return []

        # Clamp k to index size to avoid FAISS error
        ntotal = getattr(self.index, "ntotal", 0)
        if ntotal:
            k = max(1, min(k, ntotal))

        vec = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype(np.float32)

        # With normalized embeddings, IndexFlatIP scores ~= cosine similarity
        scores, idxs = self.index.search(vec, k)

        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            if 0 <= idx < len(self.meta):
                m = self.meta[idx]
                results.append(
                    {
                        "score": float(score),
                        "id": m.get("id"),
                        "artigo": m.get("artigo"),
                        "lei": m.get("lei"),
                        "url": m.get("url"),
                    }
                )
            else:
                # Defensive: unexpected positional mismatch
                results.append({"score": float(score), "id": None})
        return results
