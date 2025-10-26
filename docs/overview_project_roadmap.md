
## **Project Overview: EducaJus-BR**

An innovative **educational legal AI assistant** for Brazilian citizens and law students, focused on:

- **Legal literacy** rather than professional legal advice
- **RAG-based responses** anchored to official Brazilian legal sources
- **Multi-agent architecture** with guardrails to prevent hallucinations
- **LGPD compliance** and ethical safeguards
- Target for **OAB-PR AI Hackathon** (Dec 6-7, 2025)

---

Now I'll create a comprehensive implementation plan based on the documentation:

Let me check the current project structure and create the implementation plan:

# EducaJus-BR - Implementation Plan

Based on the comprehensive documentation analysis, here's the detailed implementation plan:

---

## **Phase 0: Project Setup & Infrastructure (Day 0 - 4h)**

### **0.1 Repository Structure**

- [ ] Initialize monorepo structure
  - `/apps/web` - Next.js frontend
  - `/apps/api` - FastAPI backend
  - `/apps/workers` - Background jobs
  - `/packages/rag` - RAG components
  - `/packages/guardrails` - Security layers
  - `/packages/agents` - Agent implementations
  - `/data/sources` - Legal data
  - `/data/indexes` - Vector indexes
  - [/docs](cci:7://file:///Users/rafaelventura/Desktop/projects/Educa_Jus_Br/docs:0:0-0:0) - Documentation

### **0.2 Development Environment**

- [ ] Set up Python virtual environment (Python 3.10+)
- [ ] Initialize Node.js project (Node 18+)
- [ ] Configure Docker & Docker Compose
- [ ] Set up Git repository with .gitignore
- [ ] Create `.env.example` for configuration

### **0.3 Core Dependencies**

```python
# Backend (requirements.txt)
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
langchain>=0.1.0
langchain-openai
python-dotenv
pydantic>=2.0.0
qdrant-client>=1.7.0
sentence-transformers
torch
faiss-cpu
python-multipart
redis
```

```json
// Frontend (package.json)
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "tailwindcss": "^3.3.0",
    "@radix-ui/react-*": "latest",
    "lucide-react": "latest"
  }
}
```

---

## **Phase 1: Data Collection & RAG Foundation (Day 0-1 - 12h)**

### **1.1 Legal Sources Collection**

- [ ] **Federal Laws** (Priority)

  - Constituição Federal 1988
  - Código de Defesa do Consumidor (Lei 8.078/90)
  - CLT (Consolidação das Leis do Trabalho)
  - Código Civil (relevant sections)
- [ ] **Regulatory Agencies**

  - ANAC Resolutions (400, 432, 569) - Air passenger rights
  - ANATEL regulations - Telecom services
  - ANS - Health insurance
  - BACEN - Consumer financial rights
- [ ] **Educational Materials**

  - CNJ cartilhas (legal education materials)
  - PROCON/Senacon consumer guides
  - Selected STF/STJ paradigmatic decisions (ementas)

### **1.2 Data Processing Pipeline**

- [ ] Create web scrapers for official sources
  - Planalto legal database
  - ANAC resolutions PDFs
  - CNJ materials
- [ ] Build text extraction utilities
  - PDF parser (PyPDF2/pdfplumber)
  - HTML cleaner (BeautifulSoup4)
  - Text normalizer
- [ ] Implement chunking strategy
  - Article-level chunking for laws
  - Section-level for regulations
  - Metadata extraction (source, date, article number, URL)

### **1.3 Vector Database Setup**

- [ ] Configure Qdrant instance (or FAISS for MVP)
- [ ] Generate embeddings
  - Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  - Or: `neuralmind/bert-base-portuguese-cased`
- [ ] Create collections with metadata filters
  - Consumer rights collection
  - Air travel collection
  - Essential services collection
- [ ] Build search interface
  - Semantic similarity search
  - Metadata filtering
  - Hybrid search (keyword + semantic)

---

## **Phase 2: Multi-Agent Architecture (Day 1-2 - 16h)**

### **2.1 Agent 1: Triagem & Ética (Layer 1 - Input)**

**Responsibilities:**

- Detect and anonymize PII (LGPD compliance)
- Classify user intent (general info vs. specific case)
- Filter malicious prompts/injections
- Redirect inappropriate requests

**Implementation:**

```python
class TriagemAgent:
    def __init__(self):
        self.pii_patterns = [
            r'\d{3}\.\d{3}\.\d{3}-\d{2}',  # CPF
            r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',  # CNPJ
            # Add more patterns
        ]

    def detect_pii(self, text: str) -> dict:
        """Detect and mask personal information"""
        pass

    def classify_intent(self, query: str) -> str:
        """Classify as 'general' or 'specific_case'"""
        pass

    def validate_input(self, query: str) -> dict:
        """Run all Layer 1 checks"""
        pass
```

**Tasks:**

- [ ] Implement PII detection (regex + NER model)
- [ ] Build intent classifier (fine-tuned BERT or GPT-based)
- [ ] Create prompt injection detector
- [ ] Design redirect messages for out-of-scope queries
- [ ] Add LGPD compliance checks

---

### **2.2 Agent 2: Busca RAG (Retrieval)**

**Responsibilities:**

- Query vector database for relevant legal sources
- Retrieve contextual chunks with metadata
- Rank results by relevance
- Return citable excerpts

**Implementation:**

```python
class BuscaAgent:
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.embedder = SentenceTransformer('model-name')

    def search(self, query: str, filters: dict = None) -> list:
        """Semantic search with metadata filtering"""
        pass

    def rerank_results(self, results: list, query: str) -> list:
        """Rerank by relevance and recency"""
        pass
```

**Tasks:**

- [ ] Implement semantic search function
- [ ] Add metadata filtering (by law type, date, topic)
- [ ] Create result reranking logic
- [ ] Build citation formatter (with URLs)
- [ ] Add caching layer (Redis) for common queries

---

### **2.3 Agent 3: Redator Didático (Layer 2 - Planning/Generation)**

**Responsibilities:**

- Generate educational responses in simple language (B1 level)
- Structure answer: summary → steps → legal basis
- Create actionable guidance
- Produce internal reasoning trace for auditing

**Implementation:**

```python
class RedatorAgent:
    def __init__(self, llm_client):
        self.llm = llm_client  # GPT-4 or Jurema-7B

    def generate_response(self, query: str, context: list) -> dict:
        """Generate structured educational response"""
        prompt = self._build_prompt(query, context)
        response = self.llm.generate(prompt)
        return self._parse_response(response)

    def _build_prompt(self, query, context):
        """Structured prompt with RAG context"""
        pass
```

**Prompt Template:**

```text
Você é um assistente educacional jurídico focado no direito brasileiro.

CONTEXTO LEGAL:
{retrieved_chunks}

PERGUNTA DO USUÁRIO:
{user_query}

INSTRUÇÕES:
1. Responda em linguagem simples (nível B1)
2. Estruture a resposta em:
   - **Resumo em 30 segundos**
   - **Passo a passo prático**
   - **Base legal** (cite artigos e links)
3. Use tom neutro e educativo
4. NÃO forneça aconselhamento individualizado
5. Cite todas as fontes usadas

RESPOSTA:
```

**Tasks:**

- [ ] Design system prompts for each domain
- [ ] Implement structured output parser
- [ ] Add language simplification checks
- [ ] Create step-by-step generator
- [ ] Build internal reasoning logger (for Layer 2 auditing)

---

### **2.4 Agent 4: Auditor de Fatos & Conformidade (Layer 3 - Output)**

**Responsibilities:**

- Validate all legal citations (articles, laws, resolutions)
- Check for prohibited content (individualized advice)
- Verify tone and bias (neutral, accessible language)
- Ensure LGPD compliance in output
- Block responses that fail checks

**Implementation:**

```python
class AuditorAgent:
    def __init__(self, source_validator):
        self.validator = source_validator

    def validate_citations(self, response: dict) -> bool:
        """Cross-check all legal references"""
        pass

    def check_compliance(self, response: dict) -> dict:
        """Run policy compliance checks"""
        checks = {
            'no_personalized_advice': self._check_advice(response),
            'neutral_tone': self._check_tone(response),
            'sources_valid': self.validate_citations(response),
            'lgpd_compliant': self._check_privacy(response)
        }
        return checks
```

**Tasks:**

- [ ] Build citation validator (lookup in indexed sources)
- [ ] Create policy checker (regex + ML classifier)
- [ ] Implement tone analyzer (sentiment + formality)
- [ ] Add readability scorer (Flesch-Kincaid PT-BR)
- [ ] Design feedback loop (send back to Redator if fails)

---

### **2.5 Agent 5: Professor (Didatização)**

**Responsibilities:**

- Generate quiz/flashcards from response
- Create simplified 1-minute summary
- Build glossary of legal terms used
- Provide "Learn More" resources

**Implementation:**

```python
class ProfessorAgent:
    def enrich_response(self, response: dict) -> dict:
        """Add educational elements"""
        response['quiz'] = self.generate_quiz(response['content'])
        response['summary_1min'] = self.create_summary(response['content'])
        response['glossary'] = self.extract_glossary(response['content'])
        return response
```

**Tasks:**

- [ ] Implement quiz generator (3 questions per topic)
- [ ] Create summary generator (ELI12 level)
- [ ] Build glossary extractor (legal terms → definitions)
- [ ] Add related topics suggester

---

### **2.6 Agent Orchestrator (Pipeline Controller)**

**Implementation:**

```python
class AgentOrchestrator:
    def __init__(self):
        self.triagem = TriagemAgent()
        self.busca = BuscaAgent(vector_db)
        self.redator = RedatorAgent(llm)
        self.auditor = AuditorAgent(validator)
        self.professor = ProfessorAgent()

    async def process_query(self, user_query: str) -> dict:
        # Layer 1: Input Guardrails
        triagem_result = self.triagem.validate_input(user_query)
        if not triagem_result['is_valid']:
            return triagem_result['redirect_message']

        # Retrieval
        context = self.busca.search(triagem_result['cleaned_query'])

        # Layer 2: Generation with Planning
        response = self.redator.generate_response(
            triagem_result['cleaned_query'],
            context
        )

        # Layer 3: Output Validation
        audit_result = self.auditor.check_compliance(response)
        if not audit_result['passed']:
            # Retry or send to HITL
            return self._handle_audit_failure(audit_result)

        # Enrichment
        final_response = self.professor.enrich_response(response)

        return final_response
```

**Tasks:**

- [ ] Build async pipeline controller
- [ ] Add retry logic for failed validations
- [ ] Implement logging at each stage
- [ ] Create performance metrics tracker
- [ ] Add error handling and fallbacks

---

## **Phase 3: Backend API (Day 2 - 8h)**

### **3.1 FastAPI Application**

**Endpoints:**

```python
# /api/v1/query
@app.post("/api/v1/query")
async def query(request: QueryRequest) -> QueryResponse:
    """Main chat endpoint"""
    pass

# /api/v1/sources
@app.get("/api/v1/sources/{source_id}")
async def get_source(source_id: str) -> SourceDetail:
    """Retrieve full source document"""
    pass

# /api/v1/feedback
@app.post("/api/v1/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """User feedback (👍/👎)"""
    pass

# /api/v1/generate-document
@app.post("/api/v1/generate-document")
async def generate_document(request: DocumentRequest) -> dict:
    """Generate complaint letter, etc."""
    pass
```

**Tasks:**

- [ ] Set up FastAPI app with CORS
- [ ] Implement request/response models (Pydantic)
- [ ] Add authentication (optional for MVP)
- [ ] Create rate limiting (prevent abuse)
- [ ] Build caching layer (Redis)
- [ ] Add comprehensive logging
- [ ] Implement health check endpoint

---

### **3.2 Background Workers**

**Tasks:**

- [ ] Create source update worker (daily legal updates)
- [ ] Build index refresh job
- [ ] Implement analytics aggregator
- [ ] Add HITL queue processor (for human review)

---

## **Phase 4: Frontend (Day 2-3 - 12h)**

### **4.1 Next.js Application**

**Pages:**

- `/` - Home with search box
- `/chat` - Conversational interface
- `/cartilha/[topic]` - Static educational guides
- `/sobre` - About the project
- `/fontes` - List of data sources

**Components:**

```typescript
// components/ChatInterface.tsx
- MessageList
- InputBox
- ResponseCard (with sources, steps, quiz)
- SourceCitation (links to laws)
- QuizCard
- GlossaryPopover

// components/ResponseDisplay.tsx
- SummarySection (30s summary)
- StepsSection (practical guidance)
- LegalBasisSection (citations with links)
- LearnMoreSection (quiz + glossary)
```

**Tasks:**

- [ ] Design UI/UX (mobile-first, accessible)
- [ ] Implement chat interface with streaming
- [ ] Build response card components
- [ ] Add source citation links (open in new tab)
- [ ] Create quiz interaction (reveal answers)
- [ ] Build glossary tooltips
- [ ] Add feedback buttons (👍/👎)
- [ ] Implement "Generate Document" feature
- [ ] Add disclaimer banner (educational purposes)
- [ ] Create responsive design (TailwindCSS)

---

### **4.2 Styling & Accessibility**

**Tasks:**

- [ ] Set up TailwindCSS + shadcn/ui
- [ ] Implement dark mode
- [ ] Ensure WCAG 2.1 AA compliance
- [ ] Add keyboard navigation
- [ ] Test with screen readers
- [ ] Optimize for mobile (< 4" screens)

---

## **Phase 5: HITL (Human-in-the-Loop) System (Day 3 - 4h)**

### **5.1 Review Queue**

**Implementation:**

```python
class HITLQueue:
    def __init__(self, redis_client):
        self.queue = redis_client

    def add_to_queue(self, query: str, response: dict, reason: str):
        """Add response to human review queue"""
        pass

    def get_pending(self) -> list:
        """Get pending reviews"""
        pass

    def approve(self, review_id: str, reviewer_notes: str):
        """Approve and release response"""
        pass
```

**Tasks:**

- [ ] Build review queue (Redis-based)
- [ ] Create reviewer dashboard (simple admin UI)
- [ ] Implement approval/rejection workflow
- [ ] Add reviewer feedback loop (train heuristics)
- [ ] Design escalation rules (what goes to HITL)

**Escalation Criteria:**

- Family law questions (custody, divorce)
- Criminal law topics
- Responses with low confidence scores
- Flagged by Auditor Agent

---

## **Phase 6: Testing & Quality Assurance (Day 3 - 6h)**

### **6.1 Unit Tests**

**Tasks:**

- [ ] Test each agent individually
  - TriagemAgent PII detection
  - BuscaAgent retrieval accuracy
  - RedatorAgent output structure
  - AuditorAgent validation logic
- [ ] Test orchestrator pipeline
- [ ] Test API endpoints
- [ ] Test frontend components

### **6.2 Integration Tests**

**Test Scenarios:**

```python
# Scenario 1: Consumer Rights - Online Purchase
query = "Comprei online e não entregaram, e agora?"
expected_topics = ["CDC", "Art. 49", "7 days return", "Procon"]

# Scenario 2: Air Travel - Delayed Flight
query = "Meu voo atrasou 4h; tenho direito a quê?"
expected_topics = ["ANAC", "Res. 400", "Alimentação", "Assistência"]

# Scenario 3: Out of Scope - Personal Legal Advice
query = "Quero processar meu ex-marido, o que devo fazer?"
expected_redirect = True
```

**Tasks:**

- [ ] Create test suite with 10-15 scenarios
- [ ] Validate response structure
- [ ] Check citation accuracy (manual verification)
- [ ] Measure readability scores (Flesch > 60)
- [ ] Test performance (p95 latency < 8s)

### **6.3 Security & Compliance Testing**

**Tasks:**

- [ ] Test LGPD compliance (no PII leakage)
- [ ] Attempt prompt injections
- [ ] Verify all citations are real
- [ ] Check for bias in responses
- [ ] Test rate limiting

---

## **Phase 7: Documentation (Day 3 - 4h)**

### **7.1 Technical Documentation**

**Files to Create:**

- [ ] `README.md` - Project overview, installation
- [ ] `docs/ARCHITECTURE.md` - System architecture diagram
- [ ] `docs/AGENTS.md` - Agent descriptions and prompts
- [ ] `docs/API.md` - API documentation
- [ ] `docs/DEPLOYMENT.md` - Deployment guide
- [ ] `docs/CONTRIBUTING.md` - Contribution guidelines
- [ ] `docs/ETHICS-LGPD.md` - Privacy and ethics considerations

### **7.2 User Documentation**

**Files to Create:**

- [ ] `docs/USER_GUIDE.md` - How to use the system
- [ ] `docs/FAQ.md` - Common questions
- [ ] `docs/LIMITATIONS.md` - What the system can/cannot do
- [ ] Disclaimer text (to display in UI)

### **7.3 Presentation Materials**

**For Hackathon Demo:**

- [ ] 5-minute pitch deck
- [ ] Live demo script
- [ ] Video demo (backup)
- [ ] One-pager (impact summary)

---

## **Phase 8: Deployment & Demo Prep (Day 3-4 - 6h)**

### **8.1 Deployment**

**Tasks:**

- [ ] Containerize with Docker
- [ ] Deploy backend (Heroku/Railway/Fly.io)
- [ ] Deploy frontend (Vercel/Netlify)
- [ ] Set up environment variables
- [ ] Configure vector DB (Qdrant Cloud or self-hosted)
- [ ] Add monitoring (Sentry for errors)

### **8.2 Demo Preparation**

**Demo Script (5 minutes):**

1. **Introduction (30s)**

   - Problem: Legal illiteracy in Brazil
   - Solution: EducaJus-BR educational assistant
2. **Demo 1: Consumer Rights (2min)**

   - Query: "Comprei online e não entregaram, e agora?"
   - Show: Response structure, citations, step-by-step, quiz
3. **Demo 2: Air Travel (1min)**

   - Query: "Meu voo atrasou 4h; tenho direito a quê?"
   - Show: ANAC resolution citation, practical guidance
4. **Demo 3: Guardrails in Action (1min)**

   - Query: Personal legal advice (out of scope)
   - Show: Redirect message, LGPD protection
5. **Closing (30s)**

   - Open-source, impact potential
   - Roadmap: more domains, mobile app

**Tasks:**

- [ ] Write demo script
- [ ] Practice presentation
- [ ] Prepare Q&A answers
- [ ] Record backup video demo
- [ ] Test on different devices

---

## **Phase 9: Post-Hackathon Roadmap**

### **+30 Days**

- [ ] Expand to 10+ legal domains
- [ ] Fine-tune Jurema-7B for better BR legal understanding
- [ ] Add analytics dashboard
- [ ] Implement A/B testing framework
- [ ] Launch public beta

### **+90 Days**

- [ ] Mobile app (React Native)
- [ ] API for third parties
- [ ] Integrations (Procon, Consumidor.gov.br)
- [ ] Learning paths (guided courses)
- [ ] Partnership with law schools and OAB

---

## **Technology Stack Summary**

### **Backend**

- **Framework:** FastAPI
- **LLM:** GPT-4 (via OpenAI API) or Jurema-7B (local)
- **Embeddings:** sentence-transformers (multilingual-MiniLM)
- **Vector DB:** Qdrant or FAISS
- **Cache:** Redis
- **Queue:** Celery + Redis

### **Frontend**

- **Framework:** Next.js 14 (App Router)
- **UI:** TailwindCSS + shadcn/ui
- **Icons:** Lucide React
- **State:** React Query

### **DevOps**

- **Containerization:** Docker + Docker Compose
- **Deployment:** Vercel (frontend) + Fly.io (backend)
- **Monitoring:** Sentry
- **CI/CD:** GitHub Actions

---

## **Success Metrics**

### **Technical**

- [ ] Precision of citations: ≥95% accurate
- [ ] Response time: p95 < 8s
- [ ] Readability: Flesch > 60
- [ ] Zero PII leakage in responses

### **Hackathon Criteria**

- [ ] **Inovação:** Multi-agent + guardrails + educational focus
- [ ] **Aplicabilidade:** Solves real citizen needs
- [ ] **Documentação:** Clear, open-source, reproducible
- [ ] **Impacto Social:** Democratizes legal knowledge

---

## **Risk Mitigation**

| Risk                 | Impact   | Mitigation                                    |
| -------------------- | -------- | --------------------------------------------- |
| LLM hallucinations   | High     | Multi-layer validation, RAG grounding         |
| Slow response time   | Medium   | Caching, async processing, model optimization |
| Legal data outdated  | High     | Daily source refresh worker, version stamps   |
| LGPD violations      | Critical | PII detection in Layer 1, no data storage     |
| Out of scope queries | Medium   | Intent classification, clear redirects        |

---

## **Team Roles (Suggested for 3-6 people)**

- **Tech Lead:** Architecture, orchestration, deployment
- **AI/ML Engineer:** RAG setup, agent prompts, model tuning
- **Backend Dev:** FastAPI, workers, database
- **Frontend Dev:** Next.js UI, components, UX
- **Legal Advisor:** Content validation, ethical guardrails (must be lawyer/law student per OAB rules)
- **Designer/PM:** Presentation, documentation, demo

---

# **Next Steps**

This plan is now ready for execution. I'm **waiting for your input** on:

1. **Team composition** - Who will work on what?
2. **Tool preferences** - Any specific LLM API (OpenAI vs. local)?
3. **Priority adjustments** - Which domains to focus on first?
4. **Timeline confirmation** - 48-72h hackathon or longer development?

Let me know how you'd like to proceed! 🚀
