---
description: Pipeline performance tuning plan
---

# Pipeline Performance Tuning (LLM + RAG)

This document captures actionable ideas to reduce end-to-end latency while preserving answer quality. It focuses on the Redator (draft generation), Professor (stylistic summarization), and RAG search.

## Current observations
- Search latency is small (≈100–300ms). The bottleneck is LLM calls.
- Redator draft (~9–10s) + Professor pass (~9–10s) leads to ≈19–20s E2E.
- Logs confirm TOP/score emphasis is working; output quality is good.

## Quick wins
- Redator (LLM input size)
  - Reduce per-source snippet length from 480 → 300–320 chars.
  - Emphasize only TOP 3 sources; render the remaining 2 as one-liners.
  - Lower `max_tokens` 700 → 550–600.
  - Ensure `temperature=0.0` and `response_format=json_object` (already in place).

- Professor (LLM output size)
  - Reduce `max_tokens` 600 → 350–400.
  - Keep strict guidance for concise `summary` and ≤5 `steps`.

- General
  - Add budget warnings in logs if an agent exceeds a target (e.g., Redator ≤6s, Professor ≤4s).
  - Consider caching draft per normalized query (read-through cache with TTL).
  - Enable streaming in UI to display the summary as soon as it’s ready.

## Prompt adjustments
- Redator
  - Keep the score markers in prompt (e.g., `[1 TOP score=0.723]`).
  - Add explicit instruction: “Deprioritize generic sources; briefly mention them in a single sentence.”
  - For queries containing key terms (e.g., “arrependimento”), strongly bias toward relevant articles (e.g., Art. 49) and related obligations.

- Professor
  - Enforce that the first sentence explicitly states the main legal institute (e.g., “Direito de Arrependimento — Art. 49”).
  - Order steps from most relevant to least relevant for the user query.

## Telemetry and observability
- Already instrumented:
  - Per-agent elapsed: `meta.busca.elapsed_ms`, `meta.redator.elapsed_ms`, `meta.professor.elapsed_ms`.
  - E2E: `meta.pipeline.elapsed_ms` (via `graph_pipeline.run`).
  - Redator draft preview and Professor summary preview in logs for comparative debugging.
- Next steps:
  - Add percentile tracking and moving averages (optional).
  - Flag slow requests when E2E > threshold, including token counts if available.

## Future roadmap
- Retry-on-parse-fail for Redator with tolerant JSON extraction (avoid heuristic fallback).
- Optional web tools (allowlist, budgeted) to enrich `extra_references` without changing `legal_basis`.
- AuditorAgent re-enable: single-pass QA; if failing, one retry to Professor/Redator.
- UI: quick replies from `follow_ups`, clearer separation for `extra_references`.

## Suggested targets (initial)
- Search: ≤300ms
- Redator: ≤6s
- Professor: ≤4s
- E2E: ≤11s

Keep this document updated as we experiment with the tuning parameters and collect timings from production-like runs.
