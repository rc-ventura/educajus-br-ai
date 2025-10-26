from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# Ensure project root on path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.busca_agent import _SEARCHER, _dedupe_results  # noqa: E402
from core.llm.client import chat_completion  # noqa: E402


def load_queries(path: Optional[Path]) -> List[str]:
    if not path:
        return []
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix in {".txt"}:
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if path.suffix in {".json"}:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [str(item) for item in data if item]
        raise ValueError("JSON file must contain a list of strings")
    raise ValueError("Unsupported query file format. Use .txt or .json")


def run_faiss(query: str, top_k: int) -> List[Dict[str, Any]]:
    if _SEARCHER is None:
        raise RuntimeError("FAISS index not loaded. Check data/indexes/cdc_faiss.")
    raw = _SEARCHER.search(query, k=top_k)
    return _dedupe_results(raw, limit=top_k)


def run_llm_rewrite(query: str, model: str, provider: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Você ajuda a reescrever perguntas de consumidores brasileiros, "
                "destacando termos relevantes do Código de Defesa do Consumidor. "
                "Responda com uma única sentença curta pensando em como pesquisar no CDC."
            ),
        },
        {
            "role": "user",
            "content": (
                'Pergunta original: "{query}"\n'
                "Reescreva como uma consulta focada em direitos do consumidor."
            ).format(query=query),
        },
    ]
    return chat_completion(messages, model=model, provider=provider, max_tokens=120)


def collect_keywords(results: Iterable[Dict[str, Any]]) -> List[str]:
    keywords: List[str] = []
    for r in results:
        for field in ("artigo", "lei", "texto"):
            value = r.get(field)
            if not value:
                continue
            tokens = [
                token.strip().lower() for token in str(value).split() if token.strip()
            ]
            keywords.extend(tokens)
    return keywords


def format_result(result: Dict[str, Any], rank: int) -> str:
    return (
        f"[{rank}] score={result.get('score', 0):.3f} | id={result.get('id')} | "
        f"artigo={result.get('artigo')} | lei={result.get('lei')}\n"
        f"    texto: {result.get('texto', '')[:240]}...\n"
    )


def experiment(
    queries: List[str], top_k: int, llm: bool, model: str, provider: str
) -> None:
    for query in queries:
        print("=" * 80)
        print(f"Consulta: {query}")
        print("-" * 80)

        rewrite: Optional[str] = None
        if llm:
            try:
                rewrite = run_llm_rewrite(query, model=model, provider=provider)
                if rewrite:
                    print(f"LLM rewrite -> {rewrite}")
                    faiss_query = rewrite
                else:
                    print("[LLM] Reescrita vazia; usando consulta original")
                    faiss_query = query
            except Exception as exc:
                print(f"[LLM] Falha na reescrita ({exc}); usando consulta original")
                faiss_query = query
        else:
            faiss_query = query

        try:
            results = run_faiss(faiss_query, top_k=top_k)
        except Exception as exc:
            print(f"[FAISS] Falha na busca ({exc})")
            continue

        hits = len(results)
        print(f"Hits: {hits}\n")
        for idx, res in enumerate(results, 1):
            print(format_result(res, idx))

        if rewrite:
            print("Palavras-chave observadas nos resultados (para análise ad-hoc):")
            sample_keywords = collect_keywords(results)[:40]
            if sample_keywords:
                print(", ".join(sample_keywords))
            else:
                print("(vazio)")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Comparar busca FAISS com/sem reescrita LLM"
    )
    parser.add_argument(
        "--queries",
        type=Path,
        help="Arquivo .txt ou .json com perguntas (uma por linha)",
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Número de resultados para mostrar"
    )
    parser.add_argument(
        "--mode",
        choices=["faiss", "faiss+llm"],
        default="faiss",
        help="faiss=consulta original | faiss+llm=reescrever antes de buscar",
    )
    parser.add_argument(
        "--model", default=None, help="Modelo LLM (usa env LLM_MODEL se vazio)"
    )
    parser.add_argument(
        "--provider", default=None, help="Provider LLM (usa env LLM_PROVIDER se vazio)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queries = load_queries(args.queries)
    if not queries:
        raise ValueError("Nenhuma consulta encontrada no arquivo fornecido.")

    llm_mode = args.mode == "faiss+llm"
    experiment(
        queries=queries,
        top_k=args.top_k,
        llm=llm_mode,
        model=args.model or "",
        provider=args.provider or "",
    )


if __name__ == "__main__":
    main()
