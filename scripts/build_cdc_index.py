#!/usr/bin/env python3
"""
Build FAISS index for CDC chunks JSONL using sentence-transformers embeddings.

Usage:
  pip install sentence-transformers faiss-cpu
  python scripts/build_cdc_index.py data/sources/cdc/cdc_chunks.jsonl data/indexes/cdc_faiss
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

import numpy as np

try:
    import faiss  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception as e:
    print("Missing dependencies. Install with: pip install sentence-transformers faiss-cpu")
    raise

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_chunks(jsonl_path: Path) -> tuple[list[str], list[dict]]:
    texts, meta = [], []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            texts.append(rec["texto"])
            meta.append({k: rec[k] for k in ("id", "artigo", "lei", "url")})
    return texts, meta


def build_index(chunks_jsonl: Path, out_dir: Path, model_name: str = MODEL_NAME) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    texts, meta = load_chunks(chunks_jsonl)

    model = SentenceTransformer(model_name)
    emb = model.encode(texts, convert_to_numpy=True, show_progress_bar=True, normalize_embeddings=True)
    emb = emb.astype(np.float32)

    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)

    faiss.write_index(index, str(out_dir / "cdc.index"))
    with (out_dir / "cdc_metadata.json").open("w", encoding="utf-8") as f:
        json.dump({"model": model_name, "meta": meta}, f, ensure_ascii=False, indent=2)
    print("Saved index and metadata to:", out_dir)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/build_cdc_index.py <chunks_jsonl> <out_dir>")
        sys.exit(1)
    chunks = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    if not chunks.exists():
        print("File not found:", chunks)
        sys.exit(2)
    build_index(chunks, out_dir)
