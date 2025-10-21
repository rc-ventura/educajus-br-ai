from __future__ import annotations
from typing import Any, Dict

try:
    from core.guardrails import style as guard_style
except ImportError:
    guard_style = None  # type: ignore


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Professor agent: ensures readability and pedagogical quality.
    
    Short-circuits if triagem blocked the query.
    MVP: placeholder style guardrail.
    """
    # Short-circuit if blocked
    if state.get("blocks", {}).get("error"):
        return state

    if guard_style and hasattr(guard_style, "ensure_readability"):
        try:
            state["blocks"] = guard_style.ensure_readability(state.get("blocks", {}))
        except Exception:
            pass

    return state
