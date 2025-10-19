#!/usr/bin/env python3
"""
Normalize CDC text extracted from PDF/HTML.
- Removes form-feed chars
- Removes lines that are only page numbers
- Collapses 3+ blank lines into 2

Usage:
  python scripts/normalize_cdc.py data/sources/cdc/cdc_clean.txt
"""
from __future__ import annotations
import sys
import re
from pathlib import Path

def normalize_text_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = text.replace("\f", "\n")
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)  # page numbers-only lines
    text = re.sub(r"\n{3,}", "\n\n", text)        # collapse extra blank lines
    path.write_text(text.strip() + "\n", encoding="utf-8")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/normalize_cdc.py <path-to-txt>")
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"File not found: {p}")
        sys.exit(2)
    normalize_text_file(p)
    print(f"Normalized: {p}")
