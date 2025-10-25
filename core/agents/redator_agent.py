from __future__ import annotations
from typing import Any, Dict, List

from core.utils.logging import get_logger


_TOP_K_DEFAULT = 5
logger = get_logger(__name__)


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Redator agent: generates educational content blocks.
    
    Short-circuits if triagem blocked the query.
    """
    # Short-circuit if blocked
    if state.get("blocks", {}).get("error"):
        logger.info("RedatorAgent: skipped due to existing block")
        return state
    logger.info("RedatorAgent: generating blocks from %d sources", len(state.get("sources") or []))

    summary_parts: List[str] = []
    steps: List[str] = []
    legal_basis: List[Dict[str, Any]] = []

    sources: List[Dict[str, Any]] = state.get("sources") or []
    for idx, src in enumerate(sources[: int(state.get("k") or _TOP_K_DEFAULT)], start=1):
        artigo = src.get("artigo") or src.get("id") or f"Fonte {idx}"
        texto = (src.get("texto") or "").strip()
        lei = src.get("lei") or "CDC"
        url = src.get("url") or ""

        if texto:
            summary_parts.append(f"• {texto}")
            steps.append(
                f"Leia o {artigo} ({lei}) para entender seus direitos nessa situação."
            )

        legal_basis.append(
            {
                "label": f"{artigo} — interpretação educativa",
                "url": url,
                "content": texto,
            }
        )

    if not summary_parts:
        summary_parts.append(
            "Não encontrei detalhes suficientes no CDC para responder com precisão."
        )

    summary = "Resumo educativo:\n" + "\n".join(summary_parts[:3])

    if not steps:
        steps = [
            "Procure identificar o artigo do CDC relacionado à situação",
            "Verifique prazos e requisitos no texto do CDC",
            "Consulte órgãos oficiais (PROCON, Consumidor.gov.br) para orientação adicional",
        ]

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
    logger.info(
        "RedatorAgent: produced summary(len=%d) steps=%d legal_basis=%d",
        len(summary),
        len(steps),
        len(legal_basis),
    )
    return state
