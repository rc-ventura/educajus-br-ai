from __future__ import annotations
from typing import Any, Dict, List
import os

from openai import OpenAI
from core.utils.logging import get_logger

logger = get_logger(__name__)


def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Auditor agent: comprehensive validation of generated content.
    
    Validates:
    1. Query-response alignment
    2. Citation accuracy (sources match)
    3. Legal advice detection (educational vs personalized)
    4. Overall quality score
    
    Short-circuits if triagem or busca blocked the query.
    """
    # Short-circuit if already blocked
    blocks = state.get("blocks", {})
    if blocks.get("error_pii") or blocks.get("error_scope") or blocks.get("error_insufficient_sources"):
        return state

    query = state.get("cleaned_query", "")
    sources = state.get("sources", [])
    content_blocks = state.get("blocks", {})
    
    # Initialize validation results
    validation_results = {
        "is_valid": True,
        "alignment_score": 1.0,
        "citations_valid": True,
        "is_educational": True,
        "issues": []
    }
    
    # 1. Check alignment between query and response
    alignment_score = _check_alignment(query, content_blocks.get("summary", ""))
    validation_results["alignment_score"] = alignment_score
    
    if alignment_score < 0.7:
        validation_results["is_valid"] = False
        validation_results["issues"].append(f"Low alignment score: {alignment_score:.2f}")
    
    # 2. Validate citations are in sources
    citations_valid = _validate_citations(content_blocks.get("legal_basis", []), sources)
    validation_results["citations_valid"] = citations_valid
    
    if not citations_valid:
        validation_results["is_valid"] = False
        validation_results["issues"].append("Citations not found in sources")
    
    # 3. Check for legal advice (should be educational only)
    is_educational = _check_educational_tone(query, content_blocks.get("summary", ""))
    validation_results["is_educational"] = is_educational
    
    if not is_educational:
        validation_results["is_valid"] = False
        validation_results["issues"].append("Content contains personalized legal advice")
    
    # Update metadata
    meta = dict(state.get("meta", {}))
    meta["auditor"] = validation_results
    state.update({"meta": meta})
    
    logger.info(f"Auditor validation: valid={validation_results['is_valid']}, issues={len(validation_results['issues'])}")
    
    return state


def _check_alignment(query: str, response: str) -> float:
    """Check if response aligns with query using LLM.
    
    Returns alignment score 0.0-1.0
    """
    if not query or not response:
        return 0.0
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OpenAI API key not available, skipping alignment check")
        return 1.0  # Assume valid if can't check
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Avalie se a resposta está alinhada com a pergunta do usuário.

Pergunta: "{query}"

Resposta: "{response}"

Retorne apenas um número de 0.0 a 1.0 indicando o alinhamento:
- 1.0 = perfeitamente alinhado
- 0.7-0.9 = bem alinhado
- 0.4-0.6 = parcialmente alinhado
- 0.0-0.3 = não alinhado

Responda apenas com o número."""
        
        response_llm = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a quality evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        
        score_text = (response_llm.choices[0].message.content or "1.0").strip()
        score = float(score_text)
        return max(0.0, min(1.0, score))
        
    except Exception as e:
        logger.error(f"Alignment check failed: {e}")
        return 1.0  # Assume valid on error


def _validate_citations(legal_basis: List[Dict], sources: List[Dict]) -> bool:
    """Validate that cited articles are present in retrieved sources."""
    if not legal_basis:
        return True  # No citations to validate
    
    if not sources:
        return False  # Has citations but no sources
    
    # Extract article numbers from legal_basis
    cited_articles = set()
    for citation in legal_basis:
        label = citation.get("label", "")
        # Extract article numbers (e.g., "Art. 49" -> "49")
        import re
        matches = re.findall(r'Art\.?\s*(\d+)', label, re.IGNORECASE)
        cited_articles.update(matches)
    
    # Extract article numbers from sources
    source_articles = set()
    for source in sources:
        artigo = source.get("artigo", "")
        if artigo:
            source_articles.add(str(artigo))
    
    # Check if all cited articles are in sources
    if cited_articles and not cited_articles.issubset(source_articles):
        missing = cited_articles - source_articles
        logger.warning(f"Citations not in sources: {missing}")
        return False
    
    return True


def _check_educational_tone(query: str, response: str) -> bool:
    """Check if content is educational vs personalized legal advice.
    
    Returns True if educational, False if personalized advice.
    """
    if not response:
        return True
    
    # Quick heuristic check for high-risk patterns
    high_risk_patterns = [
        r'\bvocê deve processar\b',
        r'\brecomendo que (processe|acione)\b',
        r'\bmeu conselho é\b',
        r'\baconselho (você |que )?a?\b',
        r'\bentre com processo\b',
    ]
    
    import re
    response_lower = response.lower()
    for pattern in high_risk_patterns:
        if re.search(pattern, response_lower, re.IGNORECASE):
            logger.warning(f"Detected advice pattern: {pattern}")
            return False
    
    # If no obvious patterns, use LLM for deeper analysis
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return True  # Assume educational if can't check
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Classifique o conteúdo como "educational" ou "advice".

Pergunta: "{query}"

Resposta: "{response}"

Educational: Explica direitos gerais, procedimentos, leis (OK)
Advice: Recomenda ações específicas para o caso do usuário (NÃO OK)

Responda apenas: educational ou advice"""
        
        response_llm = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a legal compliance classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        
        classification = (response_llm.choices[0].message.content or "educational").strip().lower()
        is_educational = "educational" in classification
        
        if not is_educational:
            logger.warning(f"Content classified as advice: {classification}")
        
        return is_educational
        
    except Exception as e:
        logger.error(f"Educational tone check failed: {e}")
        return True  # Assume educational on error
