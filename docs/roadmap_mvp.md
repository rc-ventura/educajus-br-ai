# EducaJus-BR Roadmap (MVP v0.1)

Consumer Law only (Código de Defesa do Consumidor – CDC)

---

## 1) Goals and Scope (CDC-only)

- **Objective:** Educational assistant that explains consumer rights with verified sources.
- **In-scope:** CDC (Lei 8.078/90) + cartilhas PROCON/Senacon. Few curated examples of jurisprudence (ementas) if time allows.
- **Out-of-scope:** Aconselhamento jurídico individualizado, outros domínios (trabalho, família etc.) neste MVP.
- **Output format:**
  - Resumo em 30s
  - Passo a passo prático
  - Base legal (trechos + links)
  - Quiz e glossário

---

## 2) Architecture Decisions

- **Orchestration:** LangGraph (stateful graph for multi-agent, retries, conditional routes).
- **Backend:** Python + FastAPI (thin wrapper exposing one /query endpoint).
- **RAG:** sentence-transformers embeddings + FAISS (local) or Qdrant (service). Metadata filters by source/article.
- **LLM:** OpenAI via SDK or LiteLLM adapter. Optionally Jurema-7B (local) if feasible.
- **Prototype UI:** Gradio app (single-page chat with sources). Frontend (Next.js) postponed.
- **Guardrails:** 3 layers embedded as graph nodes/validators (Input, Plan, Output).
- **Cache/Queue (optional):** Redis for caching searches and responses.

---

## 3) High-level Graph (LangGraph)

```mermaid
flowchart LR
  A[Triagem & Ética (Input)] -->|clean query / block| B[RAG Busca (CDC)]
  B --> C[Redator Didático]
  C --> D[Auditor de Fatos & Conformidade]
  D -->|ok| E[Professor (Quiz/Glossário)]
  D -- fail --> C
  E --> F[Resposta Final]
```

- **A:** PII/LGPD masking, intenção (geral x caso específico), prompt injection.
- **B:** Retrieve trechos do CDC/PROCON com metadados (artigo, link Planalto).
- **C:** Resposta didática estruturada (B1), com fontes citadas.
- **D:** Valida citações (existem? pertinentes?), bloqueia aconselhamento individual.
- **E:** Gera quiz, resumo 1min, glossário.

---

## 4) Milestones & Deliverables

- **M0 – Bootstrap (4h)**
  - Repo structure, FastAPI skeleton, Gradio stub, .env.example
- **M1 – Data (8h)**
  - Baixar/limpar CDC (Planalto) + 1–2 cartilhas PROCON/Senacon
  - Chunking por artigos/seções; metadados (artigo, URL, data)
- **M2 – RAG (6h)**
  - Embeddings + FAISS/Qdrant collection com filtros
  - API de busca com top-k + rerank simples
- **M3 – Graph v1 (10h)**
  - LangGraph com nós: Triagem → Busca → Redator → Auditor → Professor
  - Regras mínimas de guardrail (regex PII, bloqueio de conselho, verificador de citação via lookup)
- **M4 – API & UI (6h)**
  - Endpoint `/api/v1/query` integrando o grafo
  - Gradio chat: pergunta → resposta estruturada + links + quiz
- **M5 – QA & Demo (6h)**
  - Testes de precisão de citação (≥95%), leiturabilidade (Flesch PT >60)
  - Script de demo (3 cenários CDC) e gravação de backup

---

## 5) Detailed Tasks (Backlog)

- **Triagem (Input):**
  - Detectar/máscara PII (CPF/CNPJ, nomes → marcador) e normalização.
  - Classificar intenção: educacional geral vs. caso específico → redirecionar quando fora de escopo.
  - Heurísticas de prompt injection e linguagem inadequada.

- **Busca (RAG):**
  - Indexar CDC por artigos; cartilhas por seções.
  - Implementar filtros por tipo de fonte (lei/cartilha), artigo, órgão, data.
  - Formatador de citação com link do Planalto.

- **Redator:**
  - Prompt estruturado (Resumo, Passos, Base legal) em PT-BR simples (nível B1).
  - Parser do output para JSON estruturado.

- **Auditor:**
  - Validação de citações: lookup exato no índice/metadata.
  - Bloqueio de aconselhamento individual (regex/padrões).
  - Leiturabilidade e tom (neutro, inclusivo) – checagem simples.

- **Professor:**
  - Gerar 3 perguntas de quiz por resposta.
  - Glossário automático de termos do CDC.
  - Resumo 1 minuto (ELI12).

- **API/UI:**
  - FastAPI: `/api/v1/query`, `/api/v1/feedback`.
  - Gradio: chat streaming, botões “Ver fontes” e “Gerar carta PROCON (stub)”.

---

## 6) Data Sources (CDC MVP)

- **CDC (Lei 8.078/90)** – Portal do Planalto (HTML/PDF).
- **PROCON/Senacon** – Cartilhas sobre comércio eletrônico, arrependimento (art. 49), garantia, vício do produto.
- (Opcional) **Ementas** STJ selecionadas e coerentes com CDC (1–2 exemplos).

---

## 7) Policies & Guardrails (MVP)

- **Escopo:** Não oferecer valores nem estratégias para casos específicos.
- **LGPD:** Máscara automática de PII; não persistir dados sensíveis.
- **Citações:** Toda afirmação normativa deve apontar para artigo/trecho recuperado.
- **Tom:** Linguagem simples, neutra, sem jargões desnecessários.

---

## 8) Testing & Metrics

- **Precisão factual:** ≥95% de citações verificadas.
- **Leiturabilidade:** Flesch PT > 60.
- **Tempo de resposta:** p95 < 8s (com cache básico).
- **Taxa de bloqueio ético:** consultas fora de escopo corretamente redirecionadas.

---

## 9) Timeline (48–72h)

- Dia 1: M0–M2
- Dia 2: M3–M4
- Dia 3: M5 + ajustes e demo

---

## 10) Next Domains (post-MVP)

- **Voos/ANAC**, **Serviços essenciais (água/luz/telecom)**, **Compras online avançado**.
- Expandir base, prompts e verificadores; HITL básico.

---

## 11) Why LangGraph + Gradio now?

- **LangGraph:** modela fluxos de decisão/retentativas e estados internos com clareza, ideal para multi-agentes e guardrails condicionais.
- **Gradio:** entrega um protótipo clicável em horas, com chat e componentes prontos; ótimo para demo do hackathon.
- **Futuro:** Migrar UI para Next.js e manter o grafo; trocar FAISS→Qdrant; plugar HITL.
