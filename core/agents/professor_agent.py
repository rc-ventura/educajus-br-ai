from __future__ import annotations
from typing import Any, Dict, List
import time
import json

from core.utils.logging import get_logger
from core.llm.client import chat_completion, DEFAULT_MODEL, DEFAULT_PROVIDER

try:
    from core.guardrails import style as guard_style
except ImportError:
    guard_style = None  # type: ignore


logger = get_logger(__name__)


def _llm_refine(blocks: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Use LLM to craft the final educational response from a technical draft or existing blocks."""
    draft = str(blocks.get("draft") or "")
    summary_prev = str(blocks.get("summary") or "")
    steps_prev = blocks.get("steps") or []
    legal_basis = blocks.get("legal_basis") or []
    quiz_prev = blocks.get("quiz") or []
    glossary_prev = blocks.get("glossary") or []
    highlights = blocks.get("highlights") or []

    if draft:
        user_content = (
            "Você é um professor/tutor. A partir do RASCUNHO TÉCNICO abaixo, devolva EM JSON puro os blocos finais.\n"
            "Campos: summary (string, ≤5 linhas), steps (≤5 itens curtos), legal_basis (array {label,url} — PRESERVE os informados), "
            "quiz (0–2 itens {q,a}), glossary (0–5 itens {term,def}), follow_ups (2–3 perguntas curtas), "
            "extra_references (array {label,url}) opcional.\n"
            "Regras: não invente fatos; não adicione bases legais além das fornecidas; mantenha URLs e labels; "
            "melhore a redação e o tom educacional; evite redundâncias.\n\n"
            f"Pergunta: {query}\n\n"
            "Rascunho técnico:\n" + draft + "\n\n"
            "Referências legais (preservar):\n"
            + json.dumps(legal_basis, ensure_ascii=False)
            + "\n\n"
            "Destaques (opcional):\n" + json.dumps(highlights, ensure_ascii=False)
        )
    else:
        user_content = (
            "Você é um professor/tutor. Receba blocos educacionais e devolva EM JSON puro, mantendo a estrutura e os links.\n"
            "Campos: summary (string, ≤5 linhas), steps (≤5), legal_basis (array {label,url}), quiz (array {q,a}), "
            "glossary (array {term,def}), follow_ups (2–3), extra_references (array {label,url}) opcional.\n"
            "Regras: não invente fatos; preserve legal_basis (não mude labels/URLs); apenas melhore a redação.\n\n"
            f"Pergunta: {query}\n\n"
            "Blocos atuais:\n"
            f"summary=\n{summary_prev}\n\n"
            f"steps=\n{json.dumps(steps_prev, ensure_ascii=False)}\n\n"
            f"legal_basis=\n{json.dumps(legal_basis, ensure_ascii=False)}\n\n"
            f"quiz=\n{json.dumps(quiz_prev, ensure_ascii=False)}\n\n"
            f"glossary=\n{json.dumps(glossary_prev, ensure_ascii=False)}\n"
        )

    messages = [
        {
            "role": "system",
            "content": "Você revisa e melhora blocos educacionais mantendo fidelidade às fontes.",
        },
        {"role": "user", "content": user_content},
    ]

    raw = chat_completion(
        messages,
        model=DEFAULT_MODEL,
        provider=DEFAULT_PROVIDER,
        temperature=0.0,
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning(
            "ProfessorAgent: JSON decode failed (%s). Raw content: %s", exc, raw[:500]
        )
        raise

    # Ensure structure and preserve legal_basis labels/urls if present originally
    out_summary = str(data.get("summary") or (summary_prev or draft)).strip()
    out_steps = [
        str(s) for s in (data.get("steps") or (steps_prev or [])) if isinstance(s, str)
    ][:5]

    out_legal: List[Dict[str, Any]] = []
    for item in data.get("legal_basis") or legal_basis:
        if isinstance(item, dict):
            label = str(item.get("label") or "").strip()
            url = str(item.get("url") or "").strip()
            if label:
                out_legal.append({"label": label, "url": url})

    out_quiz: List[Dict[str, str]] = []
    for qa in data.get("quiz") or []:
        if isinstance(qa, dict):
            q = str(qa.get("q") or "").strip()
            a = str(qa.get("a") or "").strip()
            if q and a:
                out_quiz.append({"q": q, "a": a})
        if len(out_quiz) >= 3:
            break

    out_gloss: List[Dict[str, str]] = []
    for gl in data.get("glossary") or []:
        if isinstance(gl, dict):
            term = str(gl.get("term") or "").strip()
            d = str(gl.get("def") or "").strip()
            if term and d:
                out_gloss.append({"term": term, "def": d})
        if len(out_gloss) >= 5:
            break

    follow_ups = [str(s) for s in (data.get("follow_ups") or []) if isinstance(s, str)][
        :3
    ]
    extra_refs_out: List[Dict[str, str]] = []
    for ref in data.get("extra_references") or []:
        if isinstance(ref, dict):
            rl = str(ref.get("label") or "").strip()
            ru = str(ref.get("url") or "").strip()
            if rl and ru:
                extra_refs_out.append({"label": rl, "url": ru})
        if len(extra_refs_out) >= 3:
            break

    return {
        "summary": out_summary,
        "steps": out_steps,
        "legal_basis": out_legal or legal_basis,
        "quiz": out_quiz,
        "glossary": out_gloss,
        "follow_ups": follow_ups,
        "extra_references": extra_refs_out,
    }


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Professor agent: stylistic/editorial pass + optional enrichment.

    Short-circuits if triagem blocked the query. Robust fallback keeps original blocks.
    """
    # Short-circuit if blocked
    if state.get("blocks", {}).get("error"):
        logger.info("ProfessorAgent: skipped due to existing block")
        return state

    blocks = state.get("blocks") or {}
    if not isinstance(blocks, dict) or not blocks:
        logger.info("ProfessorAgent: no blocks to refine")
        return state

    start_ts = time.time()
    query = state.get("cleaned_query") or state.get("query") or ""
    draft_in = str(blocks.get("draft", ""))
    used_llm = False
    fallback_reason: str | None = None
    try:
        refined = _llm_refine(blocks, query)
        used_llm = True
    except Exception:
        refined = blocks
        fallback_reason = "LLM failure"

    # Apply optional guardrail after refinement
    if guard_style and hasattr(guard_style, "ensure_readability"):
        try:
            logger.info("ProfessorAgent: applying readability guard")
            refined = guard_style.ensure_readability(refined)
        except Exception:
            logger.exception("ProfessorAgent: readability guard failed")

    # Update state and meta
    meta = dict(state.get("meta", {}))
    if not used_llm and fallback_reason is None:
        fallback_reason = "LLM not attempted"
    elapsed_ms = int((time.time() - start_ts) * 1000)
    meta["professor"] = {
        "model": DEFAULT_MODEL if used_llm else "pass_through",
        "used_llm": used_llm,
        "used_tools": [],
        "external_fetch_count": 0,
        "fallback_reason": fallback_reason,
        "elapsed_ms": elapsed_ms,
    }

    state.update({"blocks": refined, "meta": meta})
    logger.info(
        "ProfessorAgent: revised (llm=%s, reason=%s) elapsed=%dms",
        str(used_llm),
        meta.get("professor", {}).get("fallback_reason"),
        elapsed_ms,
    )
    try:
        if draft_in:
            logger.info("ProfessorAgent input draft preview: %s", draft_in[:800])
        logger.info(
            "ProfessorAgent summary preview (len=%d) steps=%d follow_ups=%d",
            len(str(refined.get("summary", ""))),
            len(refined.get("steps", []) or []),
            len(refined.get("follow_ups", []) or []),
        )
        logger.info(
            "ProfessorAgent summary sample: %s", str(refined.get("summary", ""))[:600]
        )
        # Additional comparative fields
        lb = refined.get("legal_basis", []) or []
        fu = refined.get("follow_ups", []) or []
        try:
            import json as _json

            logger.info(
                "ProfessorAgent legal_basis: %s",
                _json.dumps(lb, ensure_ascii=False)[:800],
            )
        except Exception:
            logger.info("ProfessorAgent legal_basis count: %d", len(lb))
        logger.info(
            "ProfessorAgent follow_ups: %s", "; ".join([str(x) for x in fu])[:800]
        )
    except Exception:
        pass
    return state
