from __future__ import annotations
from typing import Any, Dict

from core.utils.logging import get_logger

try:
    from core.guardrails import style as guard_style
except ImportError:
    guard_style = None  # type: ignore


logger = get_logger(__name__)


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Professor agent: ensures readability and pedagogical quality.
    
    Short-circuits if triagem blocked the query.
    MVP: placeholder style guardrail.
    """
    # Short-circuit if blocked
    if state.get("blocks", {}).get("error"):
        logger.info("ProfessorAgent: skipped due to existing block")
        return state

    if guard_style and hasattr(guard_style, "ensure_readability"):
        try:
            logger.info("ProfessorAgent: applying readability guard")
            state["blocks"] = guard_style.ensure_readability(state.get("blocks", {}))
        except Exception:
            logger.exception("ProfessorAgent: readability guard failed")

    logger.info("ProfessorAgent: completed")
    return state
