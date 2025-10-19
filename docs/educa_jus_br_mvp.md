# EducaJus-BR — Assistente de Educação Jurídica com IA Segura

## Por que é inovador?

* **Foco em educação/alfabetização jurídica** (cidadão e estudante), não só produtividade de advogado.
* **Respostas sempre ancoradas em fontes oficiais** (RAG com Planalto, CNJ, ANAC, Procon, tribunais), exibindo trechos e links.
* **Guardrails** que evitam “parecer jurídico personalizado” indevido e **forçam linguagem simples** e neutra.
* **Multi-agentes** que dividem a tarefa (triagem → busca → redação → checagem → didatização).
* **HITL** : opcionalmente, um(a) mentor(a) (advogado/estudante de direito) revisa respostas sensíveis/complexas.
* **Acessibilidade e cidadania** : UX para leigos, leitura facilitada, glossário, passos práticos.

---

## Público-alvo

1. **Cidadãos** procurando orientação geral (direitos do consumidor, trabalho, família, serviços públicos).
2. **Estudantes de Direito** para estudo guiado (perguntas, flashcards, casos-modelo).
3. **Profissionais** que desejem um modo “educativo” para explicar direitos a clientes.

> **Aviso claro no produto:** conteúdo  **educacional** , não constitui aconselhamento jurídico individual (com guardrail que bloqueia “dê uma estratégia para meu caso específico”).

---

## Arquitetura (MVP em 48–72h de hackathon)

**Fluxo de agentes (pipeline):**

1. **Agente de Triagem & Ética (Layer 1)**
   * Detecta dados pessoais sensíveis (LGPD), remove/anonimiza.
   * Classifica a  **intenção** : informação geral x caso individual; se “caso individual”, reorienta para educação + sugere procurar um advogado.
   * Simplifica a pergunta para termos jurídicos controlados (ontologia leve).
2. **Agente de Busca (RAG)**
   * Consulta  **fontes oficiais** :
     * Leis: Portal do Planalto (CF/88, CDC, CLT etc.).
     * Reguladores: **ANAC** (voo),  **ANS** ,  **ANATEL** , **BACEN** (registrato / consum. financeiro).
     * **CNJ** (cartilhas, recomendações),  **Procon** /Senacon.
     * Jurisprudência básica (ementas) de STF/STJ/TJs (o que couber no MVP).
   * Retorna **trechos citáveis** + metadados (fonte, data, versão).
3. **Agente Redator Didático (Layer 2 – plano/explicação)**
   * Gera **resposta em linguagem simples** (nível B1), com:
     * **“Entenda seus direitos”** (bullets)
     * **“Passo a passo”** (o que fazer; docs; prazos; onde ir)
     * **“Base legal”** (trechos + links)
   * Produz também **um mini-plano** por trás (raciocínio/verificações) para ser auditado.
4. **Agente Auditor de Fatos & Conformidade (Layer 3)**
   * **Valida citações** : cada artigo/regra mencionada deve existir e estar  **correta e vigente** .
   * **Checa vieses/linguagem** (nada discriminatório; tom neutro).
   * **Bloqueia** qualquer aconselhamento individualizado (ex.: “no seu caso, peça R$ X”).
   * Dá *feedback* ao Redator se algo falhar; só libera quando estiver ok.
5. **Agente Professor** (Didatização & Avaliação)
   * Gera **quiz/flashcards** baseados na resposta (para fixar conteúdo).
   * Cria um **resumo de 1 minuto** (“explica como se eu tivesse 12 anos”).
   * Constrói **glossário** de termos técnicos da resposta.
6. **HITL (Opcional/Configurável)**
   * Perguntas **classificadas como “complexas/sensíveis”** (família, penal, previdenciário específico) entram em  **fila de revisão humana** .
   * O(a) revisor(a) pode aceitar/ajustar a resposta. Histórico de decisões treina heurísticas.

**Modelos**

* **Gerador principal** : modelo PT-BR jurídico (ex.: Jurema-7B) +/ou API GPT-4 para melhor fluência,  **sempre via RAG** .
* **Verificador/Auditor** : modelo menor/specialist com *regex + rules* para citações e compliance.
* **Embeddings** : sentence-transformers PT-BR (ou OpenAI embeddings), índice FAISS/Qdrant.

**Stack sugerida (hackathon-friendly)**

* Backend: **FastAPI** + **langchain/litellm** +  **qdrant/faiss** .
* Frontend: **Next.js** (chat + modo “cartilha”), acessível em mobile.
* Observabilidade: logs de consultas, *feedback* do usuário (👍/👎), salvando pares  *pergunta ↔ fontes* .

---

## Guardrails (exemplos concretos)

* **Entrada (Layer 1)**
  * **PII/LGPD** : detecção de CPF, RG, endereço → máscara automática.
  * **Escopo** : se detectar “meu caso”, responder com  *“posso explicar direitos gerais e caminhos; para aconselhamento individual, procure a Defensoria/advogado”* .
  * **Segurança** : bloqueia instruções maliciosas/prompt injection.
* **Plano (Layer 2)**
  * Lista de checagens: “toda afirmação normativa precisa de  **fonte** ”; “sem valores/estratégias prescritas”.
  * Verifica se a **jurisdição** é BR e o tema está coberto nas fontes do RAG.
* **Saída (Layer 3)**
  * **Validador de citações** : busca *exata* do artigo/súmula/ato regulatório citado.
  * **Tom & viés** : linguagem simples, neutra, sem termos técnicos desnecessários; alerta se algo soar recomendação individual.
  * **Banner educativo** + **carimbo de data** (ex.: “Atualizado em: 18/10/2025”).

---

## UX do Chat (MVP)

* **Pergunta** (ex.: “Meu voo atrasou 4h; tenho direito a quê?”)
* **Resposta** com 4 blocos:
  1. **Resumo em 30s**
  2. **Passo a passo prático** (o que pedir à Cia Aérea; canais; prazos)
  3. **Base legal** (trechos + links)
  4. **Aprenda mais** (quiz + glossário)
* **Botões:** “Ver fontes”, “Gerar carta de reclamação”, “Salvar PDF”, “Enviar para revisão humana”.

---

## Fontes para o RAG (prioridade para MVP)

* **Planalto** (CF/leis federais – endpoints estáveis).
* **ANAC (Res. 400/432)** ,  **ANATEL** , **BACEN/Senacon/Procon** (cartilhas e orientações).
* **CNJ** (cartilhas/boas práticas).
* **STJ/STF** : ementas paradigmáticas (mesmo que via *scrape* mínimo selecionado).

> Dica: começar com **3 domínios temáticos** bem documentados (ex.: consumidor/voos; serviços essenciais; compras online), para brilhar no demo.

---

## Avaliação & Métricas

* **Precisão factual** (checagem de citações: ≥95% corretas no MVP).
* **Leiturabilidade** (Flesch PT-BR alvo > 60).
* **Utilidade percebida** (NPS/CSAT no demo).
* **Tempo de resposta** (p95 < 6–8s com cache).
* **Taxa de bloqueio ético** (entradas fora de escopo corretamente reorientadas).

---

## Riscos & Mitigações

* **Mudança normativa rápida** → *jobs* de atualização do índice + carimbo de versão nas respostas.
* **Falsos positivos de LGPD** → regras + exemplos; botão “isso é dado sensível?” para aprender.
* **Excesso de expectativa (aconselhamento)** → disclaimers fortes, *guardrails* e HITL opcional.
* **Latência em fontes externas** → *caching* de trechos normativos frequentes; pré-indexação.

---

## Demonstração (script de 5 minutos)

1. **Pergunta leiga** : “Comprei online e não entregaram, e agora?”
2. EducaJus-BR responde com  **passos + base legal + carta pronta** .
3. Mostrar **verificação de citações** (marca-texto nos trechos recuperados).
4. Ativar **HITL** em um caso “sensível” (guarda/visitas): resposta diz “só educação geral” e envia à fila; revisor aprova com observação.
5. Encerrar com **quiz de 3 cards** sobre o tema — divertido e educativo.

---

## Roadmap (hackathon → pós-evento)

* **Hackathon (MVP)**
  * 3 domínios temáticos; RAG + guardrails + chat + quiz; HITL básico; repositório open-source.
* **+30 dias**
  * Mais domínios; painel de  *analytics* ; fine-tuning leve em PT-BR jurídico; acessibilidade; API pública.
* **+90 dias**
  * App mobile; integrações (Procon/Consumidor.gov.br); trilhas de aprendizado; parceria com faculdades/OAB subseções.

---

## Estrutura do repositório (open-source)

<pre class="overflow-visible!" data-start="7932" data-end="8385"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>/apps
  /web (Next.js – chat, quiz, glossário)
  /api (FastAPI – RAG, agentes, guardrails, HITL)
  /workers (indexação, atualização de fontes)
 /packages
  /rag (connectors + chunkers + embeddings)
  /guardrails (entrada/plano/saída – regras & prompts)
  /agents (triagem, busca, redator, auditor, professor)
 /data
  /sources (espelhos/ETL de leis/regulamentos)
  /indexes (qdrant/faiss)
 /docs
  /arquitetura.md /etica-lgpd.md /contribuindo.md
</span></span></code></div></div></pre>

---

## Como isso pontua no hackathon

* **Inovação** : multi-agentes + guardrails + foco educacional com RAG verificado.
* **Aplicabilidade** : usa problemas reais (voos, compras, serviços essenciais) e entrega **passo a passo** pronto.
* **Impacto social** : reduz assimetria de informação jurídica, melhora cidadania.
* **Documentação aberta** : código + guias + ética/LGPD desde o MVP.
