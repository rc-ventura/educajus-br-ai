from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict, Literal

# LangGraph
from langgraph.graph import StateGraph, END

# Agents
from core.agents import triagem_agent
from core.agents import busca_agent
from core.agents import redator_agent
from core.agents import auditor_agent
from core.agents import professor_agent


class State(TypedDict, total=False):
    query: str
    cleaned_query: str
    blocks: Dict[str, Any]
    sources: List[Dict[str, Any]]
    meta: Dict[str, Any]
    # params
    k: int
    # retry control
    retry_count: int
    max_retries: int


# Globals kept minimal for MVP
_TOP_K_DEFAULT = 5


# Conditional routing functions
def should_continue_after_triagem(state: State) -> Literal["BLOCKED", "CONTINUE"]:
    """Check if triagem blocked the query (PII or scope)."""
    blocks = state.get("blocks", {})
    if blocks.get("error_pii") or blocks.get("error_scope"):
        return "BLOCKED"
    return "CONTINUE"


def should_continue_after_busca(state: State) -> Literal["BLOCKED", "CONTINUE"]:
    """Check if busca found sufficient sources."""
    sources = state.get("sources", [])
    if len(sources) < 2:
        state["blocks"] = {
            "error_insufficient_sources": True,
            "message": "Não encontrei informações suficientes sobre sua pergunta no CDC."
        }
        return "BLOCKED"
    return "CONTINUE"


def should_continue_after_auditor(state: State) -> Literal["RETRY", "BLOCKED", "CONTINUE"]:
    """Check auditor validation and decide retry or continue."""
    meta = state.get("meta", {})
    auditor_meta = meta.get("auditor", {})
    
    # Check if validation passed
    if auditor_meta.get("is_valid", True):
        return "CONTINUE"
    
    # Check retry count
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 1)
    
    if retry_count < max_retries:
        state["retry_count"] = retry_count + 1
        return "RETRY"
    
    # Max retries exceeded - block
    state["blocks"] = {
        "error_validation_failed": True,
        "message": "Não consegui gerar uma resposta com qualidade suficiente. Tente reformular sua pergunta.",
        "issues": auditor_meta.get("issues", [])
    }
    return "BLOCKED"


# Graph definition
_graph = StateGraph(State)
_graph.add_node("triagem", triagem_agent.execute)
_graph.add_node("busca", busca_agent.execute)
_graph.add_node("redator", redator_agent.execute)
_graph.add_node("auditor", auditor_agent.execute)
_graph.add_node("professor", professor_agent.execute)

# Entry point
_graph.set_entry_point("triagem")

# Conditional edges
_graph.add_conditional_edges(
    "triagem",
    should_continue_after_triagem,
    {
        "BLOCKED": END,
        "CONTINUE": "busca"
    }
)

_graph.add_conditional_edges(
    "busca",
    should_continue_after_busca,
    {
        "BLOCKED": END,
        "CONTINUE": "redator"
    }
)

_graph.add_edge("redator", "auditor")

_graph.add_conditional_edges(
    "auditor",
    should_continue_after_auditor,
    {
        "RETRY": "redator",      # Retry generation
        "BLOCKED": END,
        "CONTINUE": "professor"
    }
)

_graph.add_edge("professor", END)

APP = _graph.compile()


def run(query: str, k: Optional[int] = None, max_retries: int = 1) -> Dict[str, Any]:
    """Convenience wrapper to execute the compiled graph.
    
    Args:
        query: User query
        k: Number of sources to retrieve
        max_retries: Maximum retry attempts for auditor validation
    """
    initial: State = {
        "query": query,
        "k": int(k or _TOP_K_DEFAULT),
        "blocks": {},
        "sources": [],
        "meta": {},
        "retry_count": 0,
        "max_retries": max_retries,
    }
    out: State = APP.invoke(initial)  # type: ignore[assignment]
    return {
        "query": out.get("query", ""),
        "cleaned_query": out.get("cleaned_query", ""),
        "blocks": out.get("blocks", {}),
        "sources": out.get("sources", []),
        "meta": out.get("meta", {}),
    }
