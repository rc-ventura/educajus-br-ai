from __future__ import annotations
import os
import sys
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

# Load env variables
load_dotenv() 

# Ensure project root on sys.path for absolute imports like `core.*`
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.agents.conversational_agent import ConversationalAgent
from core.utils.logging import get_logger

logger = get_logger(__name__)


# Initialize agent
agent = ConversationalAgent(model="gpt-4o-mini")


def chat_with_agent(message: str, history: list) -> str:
    """Process user message through ConversationalAgent.
    
    Args:
        message: User input
        history: Gradio chat history [[user_msg, bot_msg], ...]
    
    Returns:
        Bot response string
    """
    # Convert Gradio history to ConversationalAgent format
    formatted_history = []
    for user_msg, bot_msg in history:
        formatted_history.append({
            "user": user_msg,
            "assistant": bot_msg
        })
    
    try:
        # Call agent
        result = agent.chat(message, formatted_history)
        
        # Extract response
        response = result.get("response", "Desculpe, não consegui processar sua mensagem.")
        response_type = result.get("type", "unknown")
        
        # Add metadata for debugging
        if response_type == "blocked":
            meta = result.get("reason", {})
            triagem = meta.get("triagem", {})
            
            # Show which guardrail triggered
            if triagem.get("has_pii"):
                response += "\n\n🛡️ **Guardrail ativado:** PII Detection"
                findings = triagem.get("blocked", [])
                if findings:
                    response += f"\n📋 Dados detectados: {', '.join([f['type'] for f in findings])}"
            
            scope = meta.get("scope", {})
            if scope.get("domain") in ["not_law", "other_law"]:
                response += "\n\n🛡️ **Guardrail ativado:** Scope Classification"
                response += f"\n📋 Domínio detectado: {scope.get('domain')}"
        
        elif response_type == "educational":
            # Show pipeline metadata
            meta = result.get("meta", {})
            busca = meta.get("busca", {})
            if busca:
                response += f"\n\n📚 **Fontes encontradas:** {busca.get('hits', 0)}"
        
        logger.info(f"Response type: {response_type}")
        return response
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return f"❌ Erro: {str(e)}\n\nVerifique se OPENAI_API_KEY está configurada."


# Gradio interface
demo = gr.ChatInterface(
    fn=chat_with_agent,
    title="🏛️ EducaJus - Assistente CDC (Demo)",
    description="""
    **Teste os guardrails de segurança:**
    
    ✅ **Cenários de teste:**
    - 🛡️ PII: "Meu CPF é 123.456.789-09, o que faço?"
    - 🛡️ Escopo: "Quais são meus direitos trabalhistas?"
    - ✅ CDC válido: "Direito de arrependimento em compras online"
    - 💬 Saudação: "Olá, tudo bem?"
    - 🔄 Follow-up: Faça uma pergunta e depois "E se for em loja física?"
    """,
    examples=[
        "Olá, tudo bem?",
        "Quais são meus direitos em compras online?",
        "Meu CPF é 123.456.789-09, o que faço?",
        "Quais são meus direitos trabalhistas?",
        "O produto veio com defeito, o que fazer?",
    ],
    theme=gr.themes.Soft(),
    # retry_btn="🔄 Tentar novamente",
    # undo_btn="↩️ Desfazer",
    # clear_btn="🗑️ Limpar",
)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY não encontrada!")
        print("Configure com: export OPENAI_API_KEY='sua-chave'")
        sys.exit(1)
    
    print("🚀 Iniciando EducaJus Gradio Demo...")
    print("📍 Acesse: http://localhost:7860")
    print("\n🧪 Cenários de teste:")
    print("  1. PII: 'Meu CPF é 123.456.789-09, o que faço?'")
    print("  2. Escopo: 'Quais são meus direitos trabalhistas?'")
    print("  3. CDC: 'Direito de arrependimento em compras online'")
    print("\n⏹️  Pressione Ctrl+C para parar\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
    )
