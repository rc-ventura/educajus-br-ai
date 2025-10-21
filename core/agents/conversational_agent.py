from __future__ import annotations
from typing import Any, Dict, List, Optional
import os

from openai import OpenAI

from core.graph_pipeline import APP as educational_pipeline
from core.guardrails.input import InputGuard
from core.utils.logging import get_logger


logger = get_logger(__name__)
_input_guard = InputGuard()


class ConversationalAgent:
    """Hybrid conversational agent that orchestrates the educational pipeline.
    
    This agent provides a conversational interface while using the deterministic
    LangGraph pipeline as a tool for structured educational content generation.
    
    Architecture:
    - Classifies user intent (clarification, educational query, follow-up)
    - Routes to appropriate handler
    - Uses educational_pipeline as a tool for CDC queries
    - Maintains conversation context
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client: Optional[OpenAI] = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)

    def _classify_intent(self, message: str, history: List[Dict[str, str]]) -> str:
        """Classify user intent using LLM.
        
        Returns: greeting | clarification_needed | followup | educational_query
        """
        if not self.client:
            raise RuntimeError("ConversationalAgent requires OpenAI API key. Set OPENAI_API_KEY environment variable.")

        # Build context from history
        context = ""
        if history:
            context = "\n\nConversation history:\n"
            for turn in history[-2:]:  # Last 2 turns
                context += f"User: {turn.get('user', '')}\n"
                context += f"Assistant: {turn.get('assistant', '')}\n"

        prompt = f"""Classify the user's intent into exactly one category:

- greeting: Simple greetings like "olá", "oi", "bom dia"
- clarification_needed: Vague or ambiguous questions that need more details
- followup: Follow-up questions related to previous conversation
- educational_query: Questions about consumer rights (CDC)

User message: "{message}"{context}

Respond with ONLY the category name, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an intent classifier for a legal education assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=20,
            )
            
            intent = (response.choices[0].message.content or "").strip().lower()
            
            # Validate intent
            valid_intents = {"greeting", "clarification_needed", "followup", "educational_query"}
            if intent not in valid_intents:
                logger.warning(f"Invalid intent '{intent}', defaulting to educational_query")
                return "educational_query"
            
            logger.info(f"Intent classified: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Safe fallback
            return "educational_query"

    def _handle_greeting(self, message: str) -> Dict[str, Any]:
        """Handle greeting messages using LLM for natural response."""
        if not self.client:
            raise RuntimeError("ConversationalAgent requires OpenAI API key.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are EducaJus, a friendly educational assistant for Brazilian Consumer Law (CDC). "
                            "Respond warmly to greetings and briefly introduce yourself. "
                            "Keep it concise (2-3 sentences). Respond in Portuguese."
                        )
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=150,
            )
            
            greeting_response = response.choices[0].message.content or "Olá! Como posso ajudar?"
            
            return {
                "response": greeting_response,
                "type": "greeting",
                "suggestions": [
                    "Quais são meus direitos em compras online?",
                    "Como funciona o direito de arrependimento?",
                    "O que fazer se o produto veio com defeito?",
                ],
            }
            
        except Exception as e:
            logger.error(f"Greeting generation failed: {e}")
            return {
                "response": (
                    "Olá! Sou o EducaJus, assistente educacional de Direito do Consumidor. "
                    "Como posso ajudar você hoje?"
                ),
                "type": "greeting",
                "suggestions": [
                    "Quais são meus direitos em compras online?",
                    "Como funciona o direito de arrependimento?",
                    "O que fazer se o produto veio com defeito?",
                ],
            }

    def _handle_clarification(self, message: str) -> Dict[str, Any]:
        """Request clarification using LLM to generate helpful prompts."""
        if not self.client:
            raise RuntimeError("ConversationalAgent requires OpenAI API key.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are EducaJus, an educational assistant for Brazilian Consumer Law. "
                            "The user's question is vague or ambiguous. "
                            "Politely ask for clarification with 2-3 specific helpful questions. "
                            "Be friendly and educational. Respond in Portuguese."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"User asked: '{message}'\n\nAsk for clarification to help them better."
                    }
                ],
                temperature=0.7,
                max_tokens=200,
            )
            
            clarification_response = response.choices[0].message.content or (
                f"Sua pergunta '{message}' precisa de mais detalhes. Pode me contar mais?"
            )
            
            return {
                "response": clarification_response,
                "type": "clarification",
                "original_query": message,
            }
            
        except Exception as e:
            logger.error(f"Clarification generation failed: {e}")
            return {
                "response": (
                    f"Sua pergunta '{message}' é um pouco vaga. "
                    "Poderia fornecer mais detalhes? Por exemplo:\n"
                    "- Qual tipo de produto ou serviço?\n"
                    "- Qual é o problema específico?\n"
                    "- Quando isso aconteceu?"
                ),
                "type": "clarification",
                "original_query": message,
            }

    def _execute_educational_pipeline(self, query: str) -> Dict[str, Any]:
        """Execute the deterministic educational pipeline."""
        logger.info("Executing educational pipeline for query: %s", query[:50])
        
        try:
            result = educational_pipeline.invoke({
                "query": query,
                "k": 5,
                "blocks": {},
                "sources": [],
                "meta": {},
            })
            
            # Check if pipeline blocked the query
            if result.get("blocks", {}).get("error"):
                return {
                    "response": result["blocks"]["error"],
                    "type": "blocked",
                    "reason": result.get("meta", {}),
                }
            
            # Format educational response
            blocks = result.get("blocks", {})
            return {
                "response": self._format_educational_response(blocks),
                "type": "educational",
                "blocks": blocks,
                "sources": result.get("sources", []),
                "meta": result.get("meta", {}),
            }
            
        except Exception as e:
            logger.error("Pipeline execution failed: %s", e)
            return {
                "response": (
                    "Desculpe, ocorreu um erro ao processar sua pergunta. "
                    "Por favor, tente reformular ou entre em contato com o suporte."
                ),
                "type": "error",
                "error": str(e),
            }

    def _format_educational_response(self, blocks: Dict[str, Any]) -> str:
        """Format pipeline blocks into conversational response."""
        parts = []
        
        # Summary
        if blocks.get("summary"):
            parts.append(blocks["summary"])
        
        # Steps
        if blocks.get("steps"):
            parts.append("\n**Passos recomendados:**")
            for i, step in enumerate(blocks["steps"], 1):
                parts.append(f"{i}. {step}")
        
        # Legal basis
        if blocks.get("legal_basis"):
            parts.append("\n**Base legal:**")
            for ref in blocks["legal_basis"][:3]:  # Limit to top 3
                parts.append(f"- {ref.get('label', 'Referência')}")
        
        return "\n".join(parts)

    def _handle_followup(
        self, message: str, history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Handle follow-up questions using conversation context."""
        
        if not self.client:
            # Fallback: treat as new educational query
            return self._execute_educational_pipeline(message)
        
        # Build context from history
        context_messages = [
            {"role": "system", "content": (
                "You are an educational assistant for Brazilian Consumer Law (CDC). "
                "Answer follow-up questions based on the conversation history. "
                "Keep answers concise and educational."
            )}
        ]
        
        for turn in history[-3:]:  # Last 3 turns for context
            context_messages.append({"role": "user", "content": turn.get("user", "")})
            context_messages.append({"role": "assistant", "content": turn.get("assistant", "")})
        
        context_messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=context_messages,
                temperature=0.7,
                max_tokens=500,
            )
            
            answer = response.choices[0].message.content or "Desculpe, não consegui processar sua pergunta."
            
            return {
                "response": answer,
                "type": "followup",
                "context_used": len(history),
            }
            
        except Exception as e:
            logger.error("Follow-up handling failed: %s", e)
            return self._execute_educational_pipeline(message)

    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Main chat interface.
        
        Args:
            message: User message
            history: Conversation history [{"user": "...", "assistant": "..."}, ...]
        
        Returns:
            Response dict with keys: response, type, and additional metadata
        """
        history = history or []

        # Pre-intent PII guard to ensure sensitive data is blocked immediately
        triage = _input_guard.analyze(message)
        if triage.get("has_pii"):
            logger.info("Pre-triage blocked message due to PII")
            policy = {"pii": "block", "scope": "block"}
            meta = {"triagem": triage, "policy": policy}
            return {
                "response": "Falha: sua mensagem contém dado sensível (PII). Remova ou anonimize para continuar.",
                "type": "blocked",
                "reason": meta,
                "meta": meta,
            }

        # Classify intent
        intent = self._classify_intent(message, history)
        logger.info("Intent classified as: %s", intent)
        
        # Route to appropriate handler
        if intent == "greeting":
            return self._handle_greeting(message)
        
        elif intent == "clarification_needed":
            return self._handle_clarification(message)
        
        elif intent == "followup" and history:
            return self._handle_followup(message, history)
        
        else:  # educational_query
            return self._execute_educational_pipeline(message)

    def chat_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ):
        """Streaming chat interface (for future Gradio integration).
        
        Yields response chunks for real-time display.
        """
        result = self.chat(message, history)
        
        # Simple chunking for now - can be enhanced with true streaming
        response = result.get("response", "")
        chunk_size = 50
        
        for i in range(0, len(response), chunk_size):
            yield response[i:i + chunk_size]


# #TODO   1- pydantic model for  format_educacional_response
#         2- Token quotas (timeout etc)
#         3- Monitoring (metrcis) "
