from __future__ import annotations
from typing import Literal, TypedDict, Optional
import os
from openai import OpenAI
import time
from core.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

Domain = Literal["cdc", "other_law", "not_law"]


class ScopeAnalysis(TypedDict, total=False):
    is_legal: bool
    is_consumer: bool
    domain: Domain
    reason: str
    confidence: Optional[float]



class ScopeAgent:
    """Agent for scope analysis (legal vs non-legal; CDC vs other law).

    - analyze(): tries LLM (if OPENAI_API_KEY set) and falls back to heuristic.
    - classify_with_llm(): OpenAI SDK label + reason.
    """

    def classify_with_llm(self, text: str) -> tuple[Domain, str]:  
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        client = OpenAI(api_key=api_key)
        prompt = (
            "Classify the user message in exactly one of the labels: cdc | other_law | not_law. "
            "Respond only with the label, without explanations.\n\nMessage: " + (text or "")
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a legal classifier."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        label = (resp.choices[0].message.content or "").strip().lower()
        domain: Domain
        if label == "cdc":
            domain = "cdc"
        elif label == "other_law":
            domain = "other_law"
        else:
            domain = "not_law"
        return domain, f"classified_by_llm:{label}"

    def analyze(self, text: str) -> ScopeAnalysis:
        """Analyze message to decide if it is legal and, if so, whether it is Consumer Law.

        Tries LLM if API key is available; otherwise falls back to heuristic.
        Returns a structured analysis dict.
        """
        start_time = time.time()
        try:
            domain, reason = self.classify_with_llm(text)
            source = "llm"
            confidence: Optional[float] = None
        except Exception:
            #TODO: implementar heurística

            domain = "not_law"
            reason = "Heurística: nenhum indicativo jurídico encontrado."
            source = "heuristic"
            confidence = None
        
        is_legal = domain in {"cdc", "other_law"}
        is_consumer = domain == "cdc"

        elapsed = time.time() - start_time
        logger.info(f"Scope analysis: {domain} ({elapsed:.2f}s)")
        
        return {
            "is_legal": is_legal,
            "is_consumer": is_consumer,
            "domain": domain,
            "reason": f"{reason} (source={source})",
            "confidence": confidence,
        }
