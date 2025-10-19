#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import argparse

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from packages.rag.faiss_search import FaissSearcher


def main():
    parser = argparse.ArgumentParser(description="Smoke test FAISS retrieval over CDC index")
    parser.add_argument("query", type=str, help="search query text")
    parser.add_argument("--k", type=int, default=5, help="top-k results")
    parser.add_argument("--index_dir", type=str, default="data/indexes/cdc_faiss", help="path to FAISS index dir")
    args = parser.parse_args()

    searcher = FaissSearcher(args.index_dir)
    results = searcher.search(args.query, k=args.k)
    if not results:
        print("No results.")
        return
    for r in results:
        print(f"score={r['score']:.4f} | {r.get('artigo')} | {r.get('url')}")


if __name__ == "__main__":
    main()
