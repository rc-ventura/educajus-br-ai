# Multi‑Layered Agentic Guardrail Pipeline: Overview and Best Practices

## Introdução

Sistemas de inteligência artificial (IA) cada vez mais usam **agentes autônomos** capazes de
pesquisar, planejar e executar tarefas sem supervisão constante. Esses agentes, especialmente
os modelos generativos de grande porte, podem apresentar **alucinações** (respostas inventadas) ou comportamentos inseguros. Uma forma de mitigar esses riscos é por meio de  **pipelines de guardrails** ,
ou trilhos de segurança, que introduzem verificações em etapas diferentes do ciclo de um agente.

Um artigo recente de Fareed Khan, publicado em outubro de 2025 na revista  *Level Up Coding* ,
propõe um **pipeline de guardrails em várias camadas** para reduzir alucinações e riscos em
sistemas agentivos. O autor observa que, em soluções RAG (Retrieval‑Augmented Generation)
e agentivas, os guardrails são fundamentais para lidar com riscos de segurança, violações
de conformidade e prompts maliciosos[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6). Ele observa que, se uma vulnerabilidade
passar por uma camada, outra camada deverá bloqueá‑la[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).

## Estrutura geral do pipeline

O pipeline proposto segue uma estratégia de  **defesa em profundidade** . Primeiro, constrói‑se
um **agente desprotegido** para observar falhas e alucinações. Em seguida, implementa‑se
defesas em camadas independentes:

* **Construir um agente desprotegido:** observar falhas (alucinações, vulnerabilidades de segurança)
  em dados internos[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).
* **Implementar defesa em camadas:** após identificar vulnerabilidades, construir guardrails
  independentes em série[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).
* **Camada 1 – Segurança da entrada:** realizar verificações rápidas para bloquear prompts maliciosos
  ou irrelevantes antes de chegarem ao agente[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).
* **Camada 2 – Escrutínio do plano:** observar o raciocínio interno do agente para validar seu plano
  e detectar ações inseguras[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).
* **Camada 3 – Validação da saída:** verificar a exatidão de fatos e o cumprimento de políticas
  de conformidade antes de retornar a resposta ao usuário[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).

O objetivo é que cada camada atue como uma barreira independente; assim, se uma falha passar
pela primeira verificação, a segunda ou terceira camada possa interceptá‑la[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).

## Camadas de defesa em profundidade

Uma análise mais ampla de segurança para sistemas agentivos, publicada pela comunidade
Collabnix, detalha como arquitetar uma **defesa em profundidade** com várias camadas
de verificação[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense). Embora não descreva explicitamente o artigo de Fareed Khan,
essa referência complementa o conceito de guardrails, mostrando que defesas eficazes
exigem múltiplos níveis:

1. **Camada 1 – Validação de entrada**[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense)
   * Detectar **prompt injection** com classificadores especializados.
   * Normalizar diferentes codificações e idiomas antes de processar o texto[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
   * Fazer parsing estruturado para separar comandos de dados[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
2. **Camada 2 – Monitoramento do raciocínio**[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense)
   * Analisar em tempo real a **cadeia de raciocínio** do agente.
   * Aplicar detecção de anomalias em padrões de decisão[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
   * Verificar o alinhamento do objetivo (goal alignment) para garantir que o plano segue o escopo
     autorizado[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
3. **Camada 3 – Proteção da memória**[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense)
   * Isolar memorias de longo prazo e verificar a integridade de dados históricos[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
   * Controlar o acesso a operações de memória, evitando que agentes maliciosos exfiltrarem
     dados sensíveis[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
4. **Camada 4 – Segurança de ferramentas**[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense)
   * Executar códigos e scripts em ambientes **sandbox**[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
   * Limitar taxas de chamada de APIs e validar respostas de ferramentas externas[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
5. **Camada 5 – Validação da saída**[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense)
   * Verificar conformidade de políticas e prevenir vazamento de dados sensíveis[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).
   * Avaliar o risco das ações propostas pelo agente[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Layer%205%3A%20Output%20Validation).
6. **Camada 6 – Auditoria e resposta**[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Layer%206%3A%20Audit%20and%20Response)
   * Criar logs completos e implementar respostas automáticas a incidentes[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Layer%206%3A%20Audit%20and%20Response).
   * Possibilitar escalonamento humano para casos que exigem revisão manual[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Layer%206%3A%20Audit%20and%20Response).

Essa estrutura mostra que uma abordagem robusta vai além de verificar apenas a entrada e a saída.
É preciso monitorar raciocínio, memória, ferramentas usadas e manter um ciclo de auditoria
permanente[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense).

## Trade‑offs de desempenho e práticas de implantação

Implementar múltiplos guardrails implica custos de desempenho. O estudo da Collabnix
quantifica a latência adicionada por camada: validação de entrada adiciona 50–200 ms por
requisição, monitoramento heurístico 10–50 ms e validação de saída 100–300 ms, resultando em
5–15 % de overhead típico[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Security%20implementations%20introduce%20costs%3A). Isso exige  **balancear segurança e
utilidade** : filtros agressivos podem aumentar falso‑positivos e reduzir a taxa de conclusão de
tarefas[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Security%20implementations%20introduce%20costs%3A). Como solução, recomenda‑se ajustar dinamicamente o nível de
segurança conforme o contexto e otimizar caminhos críticos para reduzir impacto de latência[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=%2A%20Risk,Caching%20of%20validation%20results).

Quanto às práticas de implantação, a mesma referência sugere:

* **Fase de desenvolvimento:** red team adversarial, requisitos de segurança incorporados ao design e
  modelagem de ameaças[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Development%20Phase%3A).
* **Fase de testes:** testes de prompt injection, testes de interação entre múltiplos agentes e
  teste de estresse sob exaustão de recursos[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Testing%20Phase%3A).
* **Fase de produção:** implantação gradual com monitoramento constante e procedimentos de
  resposta a incidentes[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Production%20Phase%3A).
* **Fase de manutenção:** auditorias regulares, atualização das defesas e acompanhamento de novas
  técnicas de ataque[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Maintenance%20Phase%3A).

## Diagrama ilustrativo

A figura a seguir resume o conceito do pipeline de guardrails em três camadas principais —
validação de entrada, monitoramento do plano/raciocínio e validação de saída. Essas
etapas interligadas garantem que um agente generativo ou de RAG possa ser usado com
maior segurança.

![da52425c-da7a-487f-a714-cf103bda5c26.png](https://chatgpt.com/backend-api/estuary/content?id=file-7QoHV3FrjS5FJh4cYTu13V&ts=489119&p=fs&cid=1&sig=a99408cad95ecd61a624c166a270596ed9f0902d7f566255e9d279c7baa97e04&v=0)

## Conclusão

Implementar **guardrails em várias camadas** é uma abordagem recomendada para reduzir
**alucinações** e riscos de segurança em agentes de IA. O artigo de Fareed Khan destaca a
importância de construir um agente desprotegido para identificar vulnerabilidades e, em
seguida, aplicar defesas independentes na entrada, no planejamento e na saída[levelup.gitconnected.com](https://levelup.gitconnected.com/building-a-multi-layered-agentic-guardrail-pipeline-to-reduce-hallucinations-and-mitigate-risk-a8f73de24ea7#:~:text=Guardrails,includes%20components%20such%20as%20%E2%80%A6).

Complementando esse conceito, a análise de segurança da Collabnix mostra que uma verdadeira
defesa em profundidade precisa incluir não apenas filtros de entrada e saída, mas
também monitoramento de raciocínio, proteção de memória, segurança de ferramentas e
auditoria contínua[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=9.1%20Defense). Embora essa abordagem introduza overhead,
ela é essencial para viabilizar o uso seguro de agentes autônomos em ambientes
críticos[collabnix.com](https://collabnix.com/agentic-ai-and-security-a-deep-technical-analysis/#:~:text=Security%20implementations%20introduce%20costs%3A). Ao equilibrar desempenho e segurança, e ao adotar boas
práticas de desenvolvimento, teste e manutenção, organizações podem aproveitar
modelos generativos e agentes de IA de forma responsável e confiável.

Este relatório sintetiza as principais ideias do artigo sobre o pipeline multi-camadas de guardrails, adicionando um diagrama ilustrativo e referências complementares para fornecer contexto.
