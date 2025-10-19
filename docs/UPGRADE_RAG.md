# CDC RAG Index Improvements

## 1. Current State

- CDC artigos chunked into `data/sources/cdc/cdc_chunks.jsonl`.
- Embeddings generated with `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- FAISS IP index built via `scripts/build_cdc_index.py`.
- Metadata stored alongside index (`cdc_metadata.json`).
- Retrieval uses cosine similarity through normalized embeddings + `IndexFlatIP`.

## 2. Recommended Enhancements

- **Explicit FAISS IDs**
  - Wrap index in `faiss.IndexIDMap2(faiss.IndexFlatIP(d))`.
  - Add vectors with `add_with_ids` using numeric IDs from the chunk metadata.
  - Prevents reliance on array ordering when resolving metadata.

- **Input Validation**
  - Skip empty/invalid lines when loading JSONL.
  - Ensure each record has `id` and `texto`.
  - Log warnings when a chunk is discarded.

- **Metadata Enrichment**
  - Persist additional fields in `cdc_metadata.json`:
    - `embedding_dim`, `num_vectors`, `normalize_embeddings`
    - `created_at` timestamp
    - `model_version` or commit hash if available
    - Optional preprocessing notes

- **embeddings QA**
  - Check for non-finite values (`np.isfinite`).
  - Record the encoder device and batch size settings (CPU, MPS, GPU).

- **Scalability Options**
  - Switch to `faiss.IndexHNSWFlat` for large CDC + cartilhas corpora.
  - For very large datasets, consider IVF + PQ or migrate to Qdrant.
  - Support `encode(..., batch_size=..., device=...)` to leverage GPU/MPS.

- **Query Pipeline Alignment**
  - Ensure search uses same encoder + normalization as indexing stage.
  - Add optional cross-encoder re-ranker for top-k (later).

- **Robust Error Handling**
  - Clear error messages when dependencies missing or file not found.
  - Guard for memory errors (large corpora).

## 3. Suggested Script Update Outline

Key additions for `scripts/build_cdc_index.py`:

```python
index = faiss.IndexIDMap2(faiss.IndexFlatIP(d))
index.add_with_ids(emb, ids)

meta_payload = {
    "model": model_name,
    "embedding_dim": d,
    "num_vectors": emb.shape[0],
    "normalize_embeddings": True,
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "meta": [{"id": rid, "artigo": rec["artigo"], "lei": rec["lei"], "url": rec["url"]}],
}
```

## 4. Retrieval Smoke Test Snippet

```python
import json, faiss
from sentence_transformers import SentenceTransformer

INDEX_DIR = "data/indexes/cdc_faiss"
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
index = faiss.read_index(f"{INDEX_DIR}/cdc.index")
meta = json.load(open(f"{INDEX_DIR}/cdc_metadata.json", "r", encoding="utf-8"))
id2meta = {int(m["id"]): m for m in meta["meta"]}

def search(query: str, k: int = 5):
    vec = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(vec, k)
    return [{"score": float(s), **id2meta.get(int(i), {})} for s, i in zip(scores[0], ids[0]) if i != -1]

print(search("direito de arrependimento", 5))
```

## 5. Migration Plan (Future)

1. Apply script updates and rebuild index.
2. Validate retrieval quality with smoke tests.
3. Integrate enhanced index into LangGraph RAG node.
4. When adding cartilhas or other domains, rerun chunking + indexing.
5. For larger corpora, move to HNSW or Qdrant and update retrieval adapter.

## 6. References

- `scripts/build_cdc_index.py`
- `data/sources/cdc/cdc_chunks.jsonl`
- `data/indexes/cdc_faiss/`
- FAISS documentation on IDMap2 / HNSW / IVF
```}】
