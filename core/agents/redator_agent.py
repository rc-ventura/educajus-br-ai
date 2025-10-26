from __future__ import annotations
from typing import Any, Dict, List
import json
import time

from core.utils.logging import get_logger
from core.llm.client import chat_completion, DEFAULT_MODEL, DEFAULT_PROVIDER


_TOP_K_DEFAULT = 5
_SUMMARY_LIMIT = 320
logger = get_logger(__name__)


def _collapse_text(value: str, limit: int = _SUMMARY_LIMIT) -> str:
    """Return a single-line snippet trimmed to the limit."""
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    head = collapsed[:limit]
    truncated = head.rsplit(" ", 1)[0] if " " in head else head
    return f"{truncated}..."


def _llm_generate(query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    src_lines: List[str] = []
    for i, s in enumerate(sources, start=1):
        artigo = s.get("artigo") or s.get("id") or f"Fonte {i}"
        lei = s.get("lei") or "CDC"
        url = s.get("url") or ""
        texto = (s.get("texto") or "").strip()
        snippet = " ".join(texto.split())[:480]
        score = s.get("score")
        score_tag = f" score={score:.3f}" if isinstance(score, (int, float)) else ""
        rank_tag = " TOP" if i == 1 else ""
        src_lines.append(
            f"[{i}{rank_tag}{score_tag}] {artigo} ({lei}) | {url}\n{snippet}"
        )

    user_content = (
        "Você é um redator técnico. Leia a pergunta e as fontes e devolva EM JSON puro.\n"
        "Campos obrigatórios: draft (string, 10-15 linhas, estilo técnico, cite artigos), "
        "legal_basis (array {label:string, url:string}), highlights (array de strings, 3-6) opcional.\n"
        "Regras: use SOMENTE as fontes; não invente prazos/itens não presentes; cite artigos por nome (ex.: Art. 18). "
        "Dê MAIS PESO às fontes marcadas como TOP e/ou com maior score; trate fontes muito genéricas de forma breve. "
        "Não faça resumo curto; entregue texto rico e objetivo com base científica nas fontes.\n\n"
        f"Pergunta: {query}\n\n"
        "Fontes:\n" + "\n\n".join(src_lines)
    )

    messages = [
        {
            "role": "system",
            "content": "Você produz respostas educacionais concisas e seguras.",
        },
        {"role": "user", "content": user_content},
    ]

    raw_content = chat_completion(
        messages,
        model=DEFAULT_MODEL,
        provider=DEFAULT_PROVIDER,
        temperature=0.0,
        max_tokens=700,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        logger.warning(
            "RedatorAgent: JSON decode failed (%s). Raw content: %s",
            exc,
            raw_content[:500],
        )
        raise

    draft = str(data.get("draft") or "").strip()
    raw_basis = data.get("legal_basis") or []
    legal_basis: List[Dict[str, Any]] = []
    for item in raw_basis:
        if isinstance(item, dict):
            label = str(item.get("label") or "").strip()
            url = str(item.get("url") or "").strip()
            if label:
                legal_basis.append({"label": label, "url": url})
            if len(legal_basis) >= 5:
                break
    highlights = [
        str(x).strip() for x in (data.get("highlights") or []) if isinstance(x, str)
    ][:6]

    if not draft:
        raise RuntimeError("empty draft")

    return {
        "draft": draft,
        "legal_basis": legal_basis,
        "highlights": highlights,
    }


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Redator agent: generates educational content blocks.

    Short-circuits if triagem blocked the query.
    """
    # Short-circuit if blocked
    if state.get("blocks", {}).get("error"):
        logger.info("RedatorAgent: skipped due to existing block")
        return state
    logger.info(
        "RedatorAgent: generating blocks from %d sources",
        len(state.get("sources") or []),
    )

    start_ts = time.time()
    sources: List[Dict[str, Any]] = state.get("sources") or []
    top_sources = sources[: int(state.get("k") or _TOP_K_DEFAULT)]
    query = state.get("cleaned_query") or state.get("query") or ""

    blocks: Dict[str, Any]
    used_llm = False
    fallback_reason: str | None = None
    try:
        if top_sources and query:
            blocks = _llm_generate(query, top_sources)
            used_llm = True
        else:
            raise RuntimeError("insufficient inputs for LLM")
    except Exception:
        fallback_reason = "LLM failure"
        # Fallback: gerar um draft técnico a partir de snippets
        lines: List[str] = []
        legal_basis: List[Dict[str, Any]] = []
        for idx, src in enumerate(top_sources, start=1):
            artigo = src.get("artigo") or src.get("id") or f"Fonte {idx}"
            texto = (src.get("texto") or "").strip()
            url = src.get("url") or ""
            if texto:
                snippet = _collapse_text(texto, 260)
                lines.append(f"{artigo}: {snippet}")
            legal_basis.append({"label": artigo, "url": url})
        draft = (
            (
                "Este é um rascunho técnico baseado diretamente nos artigos encontrados. "
                + " ".join(lines[:8])
            )
            if lines
            else "Não encontrei conteúdo suficiente nas fontes para compor um rascunho."
        )
        blocks = {"draft": draft, "legal_basis": legal_basis, "highlights": lines[:6]}

    meta = dict(state.get("meta", {}))
    if not used_llm and fallback_reason is None:
        fallback_reason = "LLM not attempted"
    elapsed_ms = int((time.time() - start_ts) * 1000)
    meta["redator"] = {
        "model": DEFAULT_MODEL if used_llm else "heuristic",
        "used_llm": used_llm,
        "fallback_reason": fallback_reason,
        "mode": "draft",
        "elapsed_ms": elapsed_ms,
    }
    state.update({"blocks": blocks, "meta": meta})
    logger.info(
        "RedatorAgent: produced draft(len=%d) legal_basis=%d (llm=%s, reason=%s) elapsed=%dms",
        len(str(blocks.get("draft", ""))),
        len(blocks.get("legal_basis", []) or []),
        str(used_llm),
        meta.get("redator", {}).get("fallback_reason"),
        meta.get("redator", {}).get("elapsed_ms", -1),
    )
    preview = str(blocks.get("draft", ""))
    logger.info("=== RedatorAgent DRAFT BEGIN (len=%d) ===", len(preview))
    logger.info("%s", preview[:800])
    if len(preview) > 800:
        logger.info("[truncated %d chars]", len(preview) - 800)
    logger.info("=== RedatorAgent DRAFT END ===")
    return state
