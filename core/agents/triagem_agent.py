from __future__ import annotations
from typing import Any, Dict

from core.guardrails import input as guard_input
from core.guardrails import scope as guard_scope


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Triagem agent: PII detection + scope classification.
    
    Option B behavior: blocks on PII or out-of-scope queries.
    Records warnings (e.g., processo judicial) in meta.
    """
    q = (state.get("query") or "").strip()

    # 1) PII triage (Option B: block on PII, warn on processo)
    has_pii = False
    triage_info: Dict[str, Any] = {"has_pii": False, "has_warnings": False, "findings": []}
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

    meta = dict(state.get("meta", {}))
    policy = meta.get("policy", {"pii": "block", "scope": "block"})
    meta["policy"] = policy
    meta["triagem"] = triage_info

    if has_pii and policy.get("pii") == "block":
        state.update({
            "cleaned_query": q,
            "blocks": {"error": "Falha: sua mensagem contém dado sensível (PII). Remova ou anonimize para continuar."},
            "meta": meta,
        })
        return state

    # 2) Scope classification (Option B: block if out-of-scope)
    domain = "cdc"
    scope_meta: Dict[str, Any] = {}
    if guard_scope and hasattr(guard_scope, "ScopeAgent"):
        try:
            sa = guard_scope.ScopeAgent()
            analysis = sa.analyze(q)
            domain = analysis.get("domain", "cdc")
            scope_meta = analysis
        except Exception:
            domain = "cdc"
            scope_meta = {"domain": domain}

    meta["scope"] = scope_meta

    if domain == "not_law" and policy.get("scope") == "block":
        state.update({
            "cleaned_query": q,
            "blocks": {"error": "Pergunta fora do escopo jurídico. Sou um assistente educacional jurídico."},
            "meta": meta,
        })
        return state
    if domain == "other_law" and policy.get("scope") == "block":
        state.update({
            "cleaned_query": q,
            "blocks": {"error": "Sou especializado em Direito do Consumidor (CDC). Estamos expandindo minha inteligência para outras áreas do Direito."},
            "meta": meta,
        })
        return state

    state.update({"cleaned_query": q, "meta": meta})
    return state
