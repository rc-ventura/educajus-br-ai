from __future__ import annotations
from typing import Any, Dict, Optional

from core.guardrails import input as guard_input
from core.guardrails import scope as guard_scope
from core.utils.logging import get_logger


logger = get_logger(__name__)


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Triagem agent: PII detection + scope classification.

    Option B behavior: blocks on PII or out-of-scope queries.
    Records warnings (e.g., processo judicial) in meta.
    """
    q = (state.get("query") or "").strip()
    logger.info("TriagemAgent: start query='%s'", q[:80])

    # 1) PII triage (Option B: block on PII, warn on processo)
    has_pii = False
    triage_info: Dict[str, Any] = {
        "has_pii": False,
        "has_warnings": False,
        "findings": [],
    }
    if guard_input and hasattr(guard_input, "InputGuard"):
        try:
            ig = guard_input.InputGuard()
            triage = ig.analyze(q)
            has_pii = bool(triage.get("has_pii"))
            triage_info = {
                "has_pii": bool(triage.get("has_pii")),
                "has_warnings": bool(triage.get("has_warnings")),
                "findings": triage.get("findings", []),
                "blocked": triage.get("blocked", []),
                "warnings": triage.get("warnings", []),
            }
        except Exception:
            has_pii = False
            logger.exception("TriagemAgent: Input guard failed")

    meta = dict(state.get("meta", {}))
    policy = meta.get("policy", {"pii": "block", "scope": "block"})
    meta["policy"] = policy
    meta["triagem"] = dict(triage_info)

    blocked_error: Optional[str] = None

    if has_pii and policy.get("pii") == "block":
        logger.info(
            "TriagemAgent: blocking due to PII findings=%s", triage_info.get("blocked")
        )
        blocked_error = "Falha: sua mensagem contém dado sensível (PII). Remova ou anonimize para continuar."

    # 2) Scope classification (Option B: block if out-of-scope)
    domain = "cdc"
    scope_meta: Dict[str, Any] = {}
    if not blocked_error and guard_scope and hasattr(guard_scope, "ScopeAgent"):
        try:
            sa = guard_scope.ScopeAgent()
            analysis = sa.analyze(q)
            domain = analysis.get("domain", "cdc")
            scope_meta = analysis
        except Exception:
            domain = "cdc"
            scope_meta = {"domain": domain}
            logger.exception("TriagemAgent: Scope guard failed")

        if domain == "not_law" and policy.get("scope") == "block":
            logger.info("TriagemAgent: blocking due to scope domain=%s", domain)
            blocked_error = "Pergunta fora do escopo jurídico. Sou um assistente educacional jurídico."
        elif domain == "other_law" and policy.get("scope") == "block":
            logger.info("TriagemAgent: blocking due to scope domain=%s", domain)
            blocked_error = "Sou especializado em Direito do Consumidor (CDC). Estamos expandindo minha inteligência para outras áreas do Direito."
    else:
        scope_meta = {"domain": "cdc" if not blocked_error else "unknown"}

    meta["scope"] = scope_meta
    if blocked_error:
        meta["triagem"]["blocked_reason"] = blocked_error
        meta["triagem"]["scope_domain"] = scope_meta.get("domain")
        meta["triagem"]["blocked"] = True
    else:
        meta["triagem"]["blocked"] = False
        meta["triagem"]["scope_domain"] = scope_meta.get("domain")

    state.update({"cleaned_query": q, "meta": meta})

    if blocked_error:
        # Set explicit flags for routing consistency
        is_scope_block = meta["triagem"].get("scope_domain") in {"not_law", "other_law"}
        is_pii_block = bool(triage_info.get("has_pii"))
        state["blocks"] = {
            "error": blocked_error,
            "error_scope": is_scope_block,
            "error_pii": is_pii_block,
        }
    else:
        state.pop("blocks", None)
        logger.info(
            "TriagemAgent: passing to next node domain=%s pii=%s", domain, has_pii
        )

    return state
