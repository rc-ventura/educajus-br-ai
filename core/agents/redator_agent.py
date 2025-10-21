from __future__ import annotations
from typing import Any, Dict, List


_TOP_K_DEFAULT = 5


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Redator agent: generates educational content blocks.
    
    Short-circuits if triagem blocked the query.
    MVP: returns static placeholder content.
    """
    # Short-circuit if blocked
    if state.get("blocks", {}).get("error"):
        return state

    summary = (
        "Resumo em 30s: seus direitos do consumidor conforme o CDC e guias oficiais."
    )
    steps = [
        "Organize provas (nota fiscal, conversas, fotos)",
        "Solicite solução formal ao fornecedor",
        "Se não resolver, registre reclamação no PROCON ou Consumidor.gov.br",
    ]

    legal_basis: List[Dict[str, Any]] = []
    for r in (state.get("sources") or [])[: int(state.get("k") or _TOP_K_DEFAULT)]:
        label = r.get("artigo") or r.get("id") or "referência"
        url = r.get("url") or ""
        legal_basis.append({"label": label, "url": url})

    quiz = [
        {
            "q": "Em quantos dias posso me arrepender de compra online?",
            "a": "7 dias",
            "ref": "CDC Art. 49",
        },
    ]

    glossary = [
        {
            "term": "Vício do produto",
            "def": "Defeito ou falha de qualidade que torna o produto impróprio ou diminui seu valor.",
        }
    ]

    blocks = {
        "summary": summary,
        "steps": steps,
        "legal_basis": legal_basis,
        "quiz": quiz,
        "glossary": glossary,
    }

    state.update({"blocks": blocks})
    return state
