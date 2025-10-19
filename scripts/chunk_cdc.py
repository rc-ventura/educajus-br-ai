#!/usr/bin/env python3
"""
Create JSONL chunks from a cleaned CDC text file, splitting by article headers (e.g., "Art. 49").

Usage:
  python scripts/chunk_cdc.py data/sources/cdc/cdc_clean.txt data/sources/cdc/cdc_chunks.jsonl
"""
from __future__ import annotations
import sys
import re
import json
import datetime as dt
from pathlib import Path

PLANALTO_URL = "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm"

HEADER_RE = re.compile(r"^\s*(Art\.\s*\d+[º°\.]?[^\n]*)", re.M)


def chunk_by_article(text: str) -> list[dict]:
    headers = list(HEADER_RE.finditer(text))
    chunks = []
    for i, m in enumerate(headers):
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        chunk = text[start:end].strip()
        # Remove lines that are only page numbers
        chunk = re.sub(r"(?m)^\s*\d+\s*$", "", chunk).strip()
        header_line = m.group(1).strip().split("\n", 1)[0]
        rid = re.sub(r"[^a-z0-9]+", "-", header_line.lower()).strip("-")
        chunks.append(
            {
                "id": rid,
                "tipo": "lei",
                "lei": "8078/90",
                "artigo": header_line,
                "texto": chunk,
                "url": PLANALTO_URL,
                "collected_at": dt.date.today().isoformat(),
            }
        )
    return chunks


def main(src_txt: Path, out_jsonl: Path) -> None:
    text = src_txt.read_text(encoding="utf-8", errors="ignore").replace("\f", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    records = chunk_by_article(text)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} chunks to {out_jsonl}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/chunk_cdc.py <clean_txt> <out_jsonl>")
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(2)
    main(src, dst)
