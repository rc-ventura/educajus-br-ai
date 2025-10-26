# Plano de Evolução da Pipeline com LLM

## Objetivos
- **Qualidade pedagógica**: respostas curtas, claras, com passos práticos e base legal correta.
- **Segurança/compliance**: bloquear PII e fora de escopo de forma determinística.
- **Custo/latência**: usar LLM onde agrega mais valor (Redator/Professor), evitando chamadas inúteis.

## Arquitetura (visão geral)
- **ConversationalAgent**: interface de chat. Classifica intenção. Roteia para a pipeline educacional.
- **Triagem (determinística)**: InputGuard (PII) + ScopeAgent (escopo). Define bloqueio/continuidade e grava `meta.triagem`.
- **Busca (RAG)**: FAISS recupera fontes. Logs completos da consulta e dos hits. Opcional: reranking determinístico.
- **Redator (LLM)**: sintetiza blocos: `summary`, `steps`, `legal_basis`, `quiz`, `glossary` a partir das fontes.
- **Professor (LLM)**: revisão de estilo/clareza; padroniza tom e tamanho.
- **Auditor (LLM opcional, depois)**: QA de alinhamento e tom educacional, com 1 retry.

## Decisões-chave
- **Sem LLM na triagem para “nota”**: custo e latência desnecessários. A decisão de bloquear já é explicada de forma determinística.
- **LLM na Busca (adiado)**: só após instrumentação e reranking determinístico. Reescrita de query será avaliada com dados.
- **LLM no Redator/Professor**: maior ganho de valor (interpretação + comunicação pedagógica).

## Metadados do estado
- `blocks`: `{ error: str, error_pii: bool, error_scope: bool }`.
- `meta.triagem`: `{ has_pii: bool, scope_domain: cdc|other_law|not_law, blocked: bool, blocked_reason?: str }`.
- `meta.busca`: `{ k: int, hits: int, ids?: list[str], query_original: str, query_normalizada?: str, used_rewrite?: bool, rewrite?: str }`.
- `meta.redator`: `{ model: str, tokens?: int, elapsed?: float }`.
- `meta.professor`: `{ model: str, tokens?: int, elapsed?: float }`.

## Busca (RAG)
- **Instrumentação**: logar query original, normalizada, ids/hits, tempo.
- **Reranking determinístico** (antes da LLM):
  - BM25 ou similaridade extra sobre os top-k do FAISS.
  - Filtros simples por palavras-chave do domínio (ex.: transporte/voo).
  - Deduplicar por artigo; limitar top 3 para o Redator.
- **LLM de reescrita (opcional, fase 2)**: apenas se métricas mostrarem ganho consistente; com cache e limites de tokens.

## Redator (LLM)
- **Entrada**: pergunta do usuário + top-N fontes (título/lei/artigo/trecho/url).
- **Saída (JSON estrito)**:
  ```json
  {
    "summary": "string",
    "steps": ["string"],
    "legal_basis": [{"label": "string", "url": "string"}],
    "quiz": [{"q": "string", "a": "string"}],
    "glossary": [{"term": "string", "def": "string"}]
  }
  ```
- **Regras**:
  - Summary: 3–5 linhas, sem colar texto integral dos artigos.
  - Steps: 3–5 itens, objetivos e aplicáveis.
  - Legal basis: 2–5 referências; manter rótulos curtos e URLs.
  - Quiz/Glossário: gerar só quando evidente; caso contrário, retornar vazios.
- **Fallback**: se parsing falhar, usar heurística atual (bullets curtas) sem quebrar a UI.

## Professor (LLM)
- **Entrada**: blocos do Redator.
- **Saída**: texto revisado com:
  - Tom educativo, linguagem simples, sem aconselhamento específico.
  - Remoção de redundâncias, limite de tamanho.
  - Manter referências/links.

## Auditor (depois)
- **Checagens**: alinhamento pergunta→resposta (0.0–1.0), “educational” vs “advice”.
- **Correção**: 1 retry máximo se abaixo do limiar.

## UI
- **Triagem**: exibir apenas motivo determinístico ao bloquear (PII/escopo). Ocultar nota LLM.
- **Educacional**: mostrar resumo, passos, base legal, e contador de fontes. Toggle de debug para desenvolvedores (mostrar `meta`).

## Observabilidade
- Logs por agente: tempo, tokens, modelo, erros.
- `meta.*` preenchido sistematicamente para permitir auditoria e métricas futuras.

## Configuração
- **LiteLLM**: `LLM_PROVIDER`, `LLM_MODEL`, `LITELLM_API_BASE`.
- **Chaves por provedor**: `OPENAI_API_KEY`, etc.
- **Timeouts/retries** (futuro próximo) no cliente LiteLLM.

## Testes
- **Unitários**: mocks para Triagem/Busca/Redator/Professor; validar parsing/fallback do Redator.
- **E2E**: PII, other_law, CDC clássico (arrependimento), transporte aéreo, pergunta vaga.

## Fases de entrega (VBC)
1. Triagem determinística (feito) e roteamento com flags claras.
2. Busca com instrumentação e reranking determinístico; sem LLM.
3. Redator LLM (JSON + fallback) e revisão Professor LLM.
4. Auditor (QA) com 1 retry.
5. UI: toggle debug; melhoria de exibição.
6. Observabilidade: métricas de tokens/custo e tempos por agente.

## Critérios de aceite
- Triagem bloqueia de forma consistente e rápida; mensagens determinísticas.
- Busca mantém ou aumenta `hits` nos exemplos; top 3 relevantes após reranking/dedup.
- Redator entrega resumos curtos e passos úteis; base legal coerente.
- Professor reduz redundâncias e mantém clareza.
- Pipeline robusta com fallback sem quebrar UI.

## Riscos e mitigação
- Alucinação do Redator: restringir ao contexto das fontes; JSON estrito; fallback.
- Latência: prompts curtos; top-N pequeno; sem LLM onde não agrega (triagem/busca fase 1).
- Custos: logs de tokens/custo; evitar reescrita de busca até ter evidência de ganho.
