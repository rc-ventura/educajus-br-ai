# Multi-Agent Architecture - EducaJus CDC

## Overview

EducaJus is an educational AI assistant for Brazilian Consumer Law (Código de Defesa do Consumidor - CDC) built on a **hybrid multi-agent architecture** that combines the flexibility of conversational AI with the reliability of deterministic workflows.

## Architecture Paradigm

### Hybrid Approach: Conversational + Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  Conversational Layer                        │
│              (ConversationalAgent)                           │
│                                                              │
│  • Intent Classification                                    │
│  • Context Management                                       │
│  • Dynamic Routing                                          │
│  • Follow-up Handling                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Uses as Tool
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Deterministic Workflow Layer                    │
│                  (LangGraph Pipeline)                        │
│                                                              │
│  Triagem → Busca → Redator → Auditor → Professor           │
└─────────────────────────────────────────────────────────────┘
```

### Why Hybrid?

1. **Conversational Layer**: Handles ambiguity, clarifications, greetings, and follow-ups
2. **Workflow Layer**: Ensures consistent, auditable, and fast educational content generation
3. **Best of Both Worlds**: Flexibility where needed, determinism where critical

---

## Agent Taxonomy

### 1. Conversational Agent (Orchestrator)

**File**: `packages/agents/conversational_agent.py`

**Role**: Primary user interface and intent router

**Capabilities**:
- Intent classification (greeting, clarification, educational query, follow-up)
- Conversation context management
- Dynamic routing to appropriate handlers
- Integration point for Gradio UI

**Decision Logic**:
```python
# All decisions powered by LLM (gpt-4o-mini)
intent = classify_intent_with_llm(message, history)

if intent == "greeting":
    return generate_greeting_with_llm(message)
elif intent == "clarification_needed":
    return generate_clarification_with_llm(message)
elif intent == "followup":
    return contextual_answer_with_llm(message, history)
else:  # educational_query
    return execute_pipeline(query)
```

**Interaction Model**: Fully LLM-powered, non-deterministic, context-aware

**No Heuristics**: Unlike guardrails (which use local regex for privacy), the conversational layer uses LLM for all natural language understanding tasks

---

### 2. Workflow Agents (Specialized)

Deterministic agents orchestrated via LangGraph in a fixed pipeline.

#### 2.1 Triagem Agent

**File**: `packages/agents/triagem_agent.py`

**Role**: Input validation and scope classification

**Responsibilities**:
- **PII Detection**: Identifies sensitive data (CPF, CNPJ, email, phone)
  - Uses regex + checksum validation
  - Blocks queries with PII (Option B policy)
  - Warns on processo judicial numbers
- **Scope Classification**: Determines if query is CDC-related
  - LLM-based classification with heuristic fallback
  - Blocks non-legal or non-CDC queries
  - Records classification metadata

**Guardrails Used**:
- `InputGuard`: Local regex-based PII detection (no external API calls)
- `ScopeAgent`: LLM classification (gpt-4o-mini) with keyword fallback

**Output**:
- `meta.triagem`: PII findings, warnings, blocked items
- `meta.scope`: Domain classification, confidence, reasoning
- `blocks.error`: If query is blocked

**Interaction**: First node in pipeline, gates all downstream processing

---

#### 2.2 Busca Agent

**File**: `packages/agents/busca_agent.py`

**Role**: Retrieval-Augmented Generation (RAG) search

**Responsibilities**:
- Searches FAISS vector index of CDC articles and official guides
- Retrieves top-k most relevant legal sources
- Short-circuits if triagem blocked the query

**Technology**:
- FAISS for vector similarity search
- Embeddings: (configured in `packages/rag/faiss_search.py`)
- Index location: `data/indexes/cdc_faiss/`

**Output**:
- `sources`: List of retrieved documents with metadata
- `meta.busca`: Search parameters (k, hits)

**Interaction**: Receives cleaned query from triagem, provides sources to redator

---

#### 2.3 Redator Agent

**File**: `packages/agents/redator_agent.py`

**Role**: Educational content generation

**Responsibilities**:
- Generates structured educational blocks:
  - **Summary**: 30-second overview of consumer rights
  - **Steps**: Actionable recommendations
  - **Legal Basis**: Citations from retrieved sources
  - **Quiz**: Interactive learning questions
  - **Glossary**: Key legal terms explained

**Current Implementation**: MVP with static templates

**Future Enhancement**: LLM-powered generation using retrieved sources

**Output**:
- `blocks.summary`: Educational summary
- `blocks.steps`: Action items
- `blocks.legal_basis`: Legal references
- `blocks.quiz`: Learning questions
- `blocks.glossary`: Term definitions

**Interaction**: Consumes sources from busca, produces content for auditor

---

#### 2.4 Auditor Agent

**File**: `packages/agents/auditor_agent.py`

**Role**: Citation validation and fact-checking

**Responsibilities**:
- Validates legal citations are accurate
- Ensures references match retrieved sources
- Flags hallucinated or incorrect citations

**Guardrails Used**:
- `CitationGuard`: (stub in MVP, to be implemented)

**Output**:
- `meta.auditor.citations_ok`: Boolean validation result

**Interaction**: Validates redator output before final formatting

---

#### 2.5 Professor Agent

**File**: `packages/agents/professor_agent.py`

**Role**: Pedagogical quality and readability

**Responsibilities**:
- Ensures educational content is accessible
- Adjusts reading level for target audience
- Enhances clarity and engagement

**Guardrails Used**:
- `StyleGuard`: (stub in MVP, to be implemented)

**Output**:
- Enhanced `blocks` with improved readability

**Interaction**: Final polishing step before returning to user

---

## Data Flow

### Complete Request Flow

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│  ConversationalAgent            │
│  - Classify intent              │
│  - Route request                │
└────────────┬────────────────────┘
             │
             │ (if educational_query)
             ▼
┌─────────────────────────────────┐
│  Triagem Agent                  │
│  - Detect PII → Block if found  │
│  - Classify scope → Block if OOS│
│  - Record metadata              │
└────────────┬────────────────────┘
             │
             │ (if passed)
             ▼
┌─────────────────────────────────┐
│  Busca Agent                    │
│  - Search FAISS index           │
│  - Retrieve top-k sources       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Redator Agent                  │
│  - Generate summary             │
│  - Create action steps          │
│  - Format legal basis           │
│  - Add quiz & glossary          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Auditor Agent                  │
│  - Validate citations           │
│  - Check factual accuracy       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Professor Agent                │
│  - Ensure readability           │
│  - Enhance pedagogy             │
└────────────┬────────────────────┘
             │
             ▼
    Educational Response
             │
             ▼
┌─────────────────────────────────┐
│  ConversationalAgent            │
│  - Format for user              │
│  - Add suggestions              │
└─────────────────────────────────┘
             │
             ▼
         User Output
```

---

## Guardrails Architecture

### Input Guardrails

#### InputGuard (`packages/guardrails/input.py`)

**Purpose**: Protect user privacy and system integrity

**Detection Methods**:
- **Regex Patterns**: CPF, CNPJ, email, phone, processo judicial
- **Checksum Validation**: Brazilian tax ID validation algorithms
- **Policy-Based Severity**:
  - `block`: CPF, CNPJ, email, phone → reject query
  - `warn`: processo number → allow with warning

**Privacy Principle**: **Never send PII to external APIs**
- All detection is local
- No LLM calls with sensitive data
- Masking happens before any external processing

**Output**:
```python
{
    "has_pii": bool,
    "has_warnings": bool,
    "findings": [...],
    "blocked": [...],
    "warnings": [...],
    "masked_text": str
}
```

---

#### ScopeAgent (`packages/guardrails/scope.py`)

**Purpose**: Ensure queries are within CDC domain

**Classification**:
- `cdc`: Consumer law → proceed
- `other_law`: Different legal area → block with educational message
- `not_law`: Non-legal query → block

**Methods**:
1. **LLM Classification** (primary): gpt-4o-mini with structured prompt
2. **Heuristic Fallback**: Keyword matching if LLM unavailable

**Keywords**:
- CDC: consumidor, fornecedor, produto, garantia, PROCON, etc.
- Other Law: trabalhista, penal, tributário, previdenciário, etc.

**Output**:
```python
{
    "is_legal": bool,
    "is_consumer": bool,
    "domain": "cdc" | "other_law" | "not_law",
    "reason": str,
    "confidence": float | None
}
```

---

### Output Guardrails

#### CitationGuard (`packages/guardrails/citation.py`)

**Purpose**: Prevent hallucinated legal references

**Status**: Stub (to be implemented)

**Planned Features**:
- Cross-reference citations with retrieved sources
- Validate article numbers against CDC corpus
- Flag suspicious or non-existent references

---

#### StyleGuard (`packages/guardrails/style.py`)

**Purpose**: Ensure pedagogical quality

**Status**: Stub (to be implemented)

**Planned Features**:
- Reading level assessment (Flesch-Kincaid)
- Jargon detection and simplification
- Engagement metrics (questions, examples, analogies)

---

## State Management

### LangGraph State Schema

```python
class State(TypedDict, total=False):
    query: str              # Original user query
    cleaned_query: str      # Post-triagem query
    blocks: Dict[str, Any]  # Educational content blocks
    sources: List[Dict]     # Retrieved legal sources
    meta: Dict[str, Any]    # Metadata from all agents
    k: int                  # Number of sources to retrieve
```

### Metadata Structure

```python
meta = {
    "policy": {
        "pii": "block",
        "scope": "block"
    },
    "triagem": {
        "has_pii": bool,
        "has_warnings": bool,
        "findings": [...],
        "blocked": [...],
        "warnings": [...]
    },
    "scope": {
        "domain": str,
        "reason": str,
        "confidence": float | None
    },
    "busca": {
        "k": int,
        "hits": int
    },
    "auditor": {
        "citations_ok": bool
    }
}
```

---

## Technology Stack

### Core Framework
- **LangGraph**: Workflow orchestration
- **OpenAI SDK**: LLM integration (gpt-4o-mini)
- **Python 3.10+**: Runtime

### Retrieval
- **FAISS**: Vector similarity search
- **Custom embeddings**: (configured in RAG module)

### Guardrails
- **Regex**: Local PII detection
- **LLM**: Scope classification
- **Custom validators**: CPF/CNPJ checksums

### Utilities
- **Centralized logging**: `packages/utils/logging.py`
- **Type safety**: TypedDict, type hints

---

## Agent Interaction Patterns

### Pattern 1: Sequential Pipeline (Current)

**Use Case**: Standard educational query

**Flow**: Triagem → Busca → Redator → Auditor → Professor

**Characteristics**:
- Deterministic
- Fast (no decision overhead)
- Auditable
- Consistent output

**Example**:
```
User: "Comprei um celular com defeito, o que fazer?"
→ Triagem: ✓ No PII, ✓ CDC scope
→ Busca: Retrieved CDC Art. 18, 26
→ Redator: Generated steps + summary
→ Auditor: ✓ Citations valid
→ Professor: ✓ Readability OK
→ Response: Educational content
```

---

### Pattern 2: Conversational Routing (Implemented)

**Use Case**: Ambiguous or follow-up queries

**Flow**: ConversationalAgent → (classify) → Pipeline or Direct Answer

**Characteristics**:
- Non-deterministic
- Context-aware
- Flexible
- Higher latency

**Example**:
```
User: "E se for online?"
→ ConversationalAgent: Detects follow-up
→ Uses conversation history
→ Direct LLM answer about online purchases
→ Response: Contextual answer
```

---

### Pattern 3: Early Termination (Implemented)

**Use Case**: Blocked queries (PII or out-of-scope)

**Flow**: Triagem → (block) → Error Response

**Characteristics**:
- Fast failure
- Privacy-preserving
- Educational feedback

**Example**:
```
User: "Meu CPF 123.456.789-00 foi usado indevidamente"
→ Triagem: ✗ PII detected
→ Response: "Detectamos dado sensível. Remova CPF para continuar."
```

---

## Future Enhancements

### Phase 2: Enhanced Conversational Layer

- [ ] Multi-turn clarification dialogs
- [ ] Proactive suggestions based on query patterns
- [ ] Sentiment analysis for user frustration detection
- [ ] Multilingual support (Spanish, English)

### Phase 3: Advanced Redator

- [ ] LLM-powered content generation using retrieved sources
- [ ] Personalized explanations based on user profile
- [ ] Case study generation from real PROCON data
- [ ] Interactive decision trees

### Phase 4: Production Guardrails

- [ ] Implement CitationGuard with source verification
- [ ] Implement StyleGuard with readability metrics
- [ ] Add ToxicityGuard for user input
- [ ] Add BiasGuard for fair legal guidance

### Phase 5: Adaptive Learning

- [ ] User feedback loop for content quality
- [ ] A/B testing framework for response variations
- [ ] Reinforcement learning for routing optimization
- [ ] Knowledge base updates from new legislation

---

## Integration Points

### Gradio UI Integration

The `ConversationalAgent` is designed for seamless Gradio integration:

```python
import gradio as gr
from packages.agents.conversational_agent import ConversationalAgent

agent = ConversationalAgent()

def chat_interface(message, history):
    # Convert Gradio history format
    formatted_history = [
        {"user": h[0], "assistant": h[1]}
        for h in history
    ]

    result = agent.chat(message, formatted_history)
    return result["response"]

demo = gr.ChatInterface(
    fn=chat_interface,
    title="EducaJus - Assistente CDC",
    description="Aprenda sobre seus direitos do consumidor"
)

demo.launch()
```

### API Integration

For REST API deployment:

```python
from fastapi import FastAPI
from packages.agents.conversational_agent import ConversationalAgent

app = FastAPI()
agent = ConversationalAgent()

@app.post("/chat")
def chat_endpoint(message: str, history: list = []):
    return agent.chat(message, history)
```

---

## Testing Strategy

### Unit Tests

- **Per-Agent Testing**: Each agent has isolated tests
  - `test_triagem_agent.py`: PII detection, scope classification
  - `test_busca_agent.py`: RAG retrieval accuracy
  - `test_redator_agent.py`: Content generation quality
  - `test_auditor_agent.py`: Citation validation
  - `test_professor_agent.py`: Readability metrics

### Integration Tests

- **Pipeline Tests**: End-to-end workflow validation
  - Valid CDC query → complete educational response
  - PII query → blocked with appropriate message
  - Out-of-scope query → blocked with redirect

### Conversational Tests

- **Intent Classification**: Accuracy of routing decisions
- **Context Handling**: Multi-turn conversation coherence
- **Fallback Behavior**: Graceful degradation when LLM unavailable

---

## Performance Considerations

### Latency Budget

| Component | Target | Current |
|-----------|--------|---------|
| Triagem (PII) | <100ms | ~50ms (regex) |
| Triagem (Scope) | <500ms | ~300ms (LLM) |
| Busca | <200ms | ~150ms (FAISS) |
| Redator | <100ms | ~50ms (template) |
| Auditor | <100ms | TBD |
| Professor | <100ms | TBD |
| **Total Pipeline** | **<1s** | **~550ms** |
| Conversational Layer | <1s | ~800ms |

### Optimization Strategies

1. **Caching**: Cache scope classifications for common queries
2. **Batch Processing**: Group similar queries for LLM efficiency
3. **Async Execution**: Parallelize independent agents (future)
4. **Model Selection**: Use faster models for non-critical tasks

---

## Security & Privacy

### Privacy Principles

1. **Local-First PII Detection**: Never send sensitive data to external APIs
2. **Data Minimization**: Only store anonymized query patterns
3. **Transparency**: Clear user communication about data handling
4. **Right to Deletion**: Support for conversation history removal

### Security Measures

1. **Input Validation**: All user input sanitized before processing
2. **Output Filtering**: Prevent injection attacks in generated content
3. **API Key Management**: Environment-based secrets, never hardcoded
4. **Audit Logging**: All agent decisions logged for review

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Gradio UI                            │
│              (User Interface Layer)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ConversationalAgent                         │
│           (Orchestration Layer)                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph Pipeline                          │
│           (Workflow Execution Layer)                     │
│                                                          │
│  ┌──────────┐  ┌──────┐  ┌────────┐  ┌────────┐       │
│  │ Triagem  │→ │Busca │→ │Redator │→ │Auditor │→ ...  │
│  └──────────┘  └──────┘  └────────┘  └────────┘       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 External Services                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  OpenAI API  │  │  FAISS Index │  │   Logging    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Conclusion

The EducaJus multi-agent architecture represents a **pragmatic hybrid approach** that balances:

- **Flexibility** (conversational layer) with **reliability** (workflow layer)
- **User experience** (natural interaction) with **performance** (fast responses)
- **Innovation** (LLM-powered) with **safety** (guardrails and validation)

This architecture is designed to **scale** from MVP to production while maintaining:
- Clear separation of concerns
- Testability at every layer
- Privacy and security by design
- Extensibility for future enhancements

The system is ready for **Gradio integration** and provides a solid foundation for building a trustworthy educational AI assistant for Brazilian consumers.
