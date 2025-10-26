---
description: AuditorAgent implementation report (design, placement, trade-offs)
---

# AuditorAgent – Implementation Report

This report outlines a pragmatic, extensible design for an AuditorAgent – the pipeline “brain” that reduces hallucinations, validates structure, and improves reliability without excessive latency.

## 1) Objectives and Non‑Goals
- Objectives
  - Anti‑hallucination: ensure claims are grounded in retrieved sources.
  - Structural validation: verify JSON contracts for blocks (summary, steps, legal_basis, etc.).
  - Policy & style checks: readability, tone, length, list sizes.
  - Telemetry: produce machine‑readable issues and scores; drive targeted retries.
  - Low overhead: run cheap deterministic checks first; reserve LLM audits for flagged cases.
- Non‑Goals
  - Not a replacement for guardrails/triage.
  - Not a full legal reasoner. Evidence must come from retrieved sources.

## 2) Placement in Pipeline
- Stages in current pipeline: triagem → busca → redator → professor (→ END)
- Auditor insertion points:
  1. After Busca: evaluate source quality/diversity; detect retrieval drift.
  2. After Redator: verify draft grounding (citations, coverage); JSON conformance.
  3. After Professor: validate structure, preserve legal_basis, final QA.
  4. E2E: latency, completeness, adherence to policy budgets.
- Modes per edge:
  - Advisory (non‑blocking): logs and meta.issues only.
  - Gate (blocking): set `blocks.error_*` and stop.
  - Retry: emit targeted feedback, reroute to the producing node once.

## 3) Operating Modes (Trade‑offs)
- Synchronous Gate: precise but adds latency. Use sparingly on risky outputs.
- Parallel Advisory: run in background; if violations are severe, trigger visible warnings next turn.
- Hybrid Budgeted: deterministic checks always; LLM checks only when risk_score ≥ threshold.

## 4) Checks by Stage
- After Busca (Search Audit)
  - Top‑K relevance distribution (scores monotonicity, min score threshold).
  - Diversity: unique artigos/leis; dedupe effectiveness.
  - Coverage expectation: does the query imply a key article (e.g., “arrependimento” → Art. 49) present in hits?
  - Output: `audit.search = { ok, issues[], scores[], diversity, missing_expected[] }`.

- After Redator (Draft Audit)
  - JSON validity and required keys present.
  - Citation coverage: claims reference at least one retrieved fonte; detect external claims.
  - No fabrication: `legal_basis` labels/URLs must match sources or known allowlist.
  - Density and scope: draft centers on highest‑score sources; generic sources briefly mentioned.
  - Output: `audit.redator = { ok, issues[], unsupported_spans[], coverage_score, suggestions }`.

- After Professor (Final Blocks Audit)
  - Structure: summary ≤ 5 lines; steps ≤ 5 items; quiz/glossary bounds; follow_ups 2–3.
  - Invariants: `legal_basis` preserved (labels/URLs unchanged).
  - Tone/clarity: readability within target grade; no redundancy.
  - Output: `audit.professor = { ok, issues[], structure_lints[], invariants_ok }`.

- E2E Audit
  - Latency budgets per agent and total; flag slow paths.
  - Consistency: summary mentions the core institute detected (e.g., Art. 49 when applicable).
  - Output: `audit.pipeline = { ok, elapsed_ms, budget_flags[] }`.

## 5) Plan‑First Option (LLM “Work Plan”)
- Flow (optional, feature‑flagged):
  1. Planner LLM produces a JSON plan: objectives, key articles expected, outline (claims ↔ sources), success criteria.
  2. Redator executes the plan to produce `draft`.
  3. Auditor compares draft vs plan: coverage, deviations, missing key articles.
  4. If critical gaps, emit targeted feedback; optional single retry to Redator.
- Benefits: reduces drift, enables precise auditor diffs.
- Cost: +1 LLM call for planning; use only for complex queries (risk‑based trigger).

## 6) Parallel Auditing Pattern
- Deterministic guards run inline (JSON schema, invariants, sizes).
- LLM auditor runs in parallel when needed:
  - Input: sources (snippets + ids), produced text (draft/summary), and the plan if available.
  - Output: structured checklist with evidence pointers (hit ids, sentences).
- Conflict resolution: if auditor flags high‑severity, pipeline can short‑circuit or issue a targeted retry with minimal prompt delta.

## 7) Data Contracts (Schemas)
- Audit Report (common)
```json
{
  "ok": true,
  "severity": "info|warn|error",
  "issues": [
    { "code": "UNSUPPORTED_CLAIM", "msg": "…", "evidence": ["hit#1", "span:…"], "suggested_fix": "…", "severity": "error" }
  ],
  "scores": { "coverage": 0.92, "style": 0.8 },
  "elapsed_ms": 312
}
```
- Planner Plan
```json
{
  "objectives": ["Answer user question re: …"],
  "key_articles": ["Art. 49"],
  "outline": [
    { "claim": "Consumers can withdraw within 7 days", "evidence": ["Art. 49"], "priority": 1 },
    { "claim": "Full refund obligation", "evidence": ["Art. 49 parágrafo único"], "priority": 1 }
  ],
  "success_criteria": ["Mentions Art. 49 in the first sentence", "≤5 steps"]
}
```

## 8) API Surface
- `auditor_agent.execute(state) -> state`
  - Reads: `state.query`, `state.sources`, `state.blocks`, `state.meta.*`
  - Writes: `meta.audit = { search?, redator?, professor?, pipeline? }`, `meta.audit.elapsed_ms`.
  - On gating failure: set `state.blocks.error_validation_failed` with `issues`.
- LLM call (optional): `audit_llm.check({ sources, draft, blocks, plan, policy }) -> audit_report`.

## 9) Retry and Policies
- Policy config:
  - `mode`: advisory | gate | retry_once
  - `thresholds`: coverage_min, max_elapsed_ms per agent, required_articles_by_keyword
  - `sampling`: audit every Nth request with heavy LLM checks
- Retry strategy:
  - Retry only the producing node with targeted feedback (`suggested_fix` from auditor).
  - One retry max; otherwise advisory.

## 10) Telemetry & Observability
- Add `meta.audit.*.elapsed_ms` and `ok` flags.
- Log compact issue summaries: codes + counts + top evidence.
- Optionally emit metrics (counters/timers) to a dashboard later.

## 11) Phased Implementation Plan
- Phase 1 (MVP)
  - Deterministic validators:
    - JSON schema for blocks, size bounds, invariant `legal_basis`.
    - Search audit: scores present, diversity, expected article present by keyword map.
  - `auditor_agent.execute` after Redator and after Professor (advisory mode).
  - Telemetry: `meta.audit` with `ok`, `issues`, `elapsed_ms`.

- Phase 2
  - LLM checklist auditor (budgeted, risk‑based) for Redator grounding and Professor structure.
  - Optional single retry with targeted feedback.
  - Planner (feature flag) for complex queries.

- Phase 3
  - Full gating on high severity.
  - Sampling & alerting; slow‑path profiling; token accounting.

## 12) Risks & Mitigations
- Latency inflation: mitigate with risk‑based triggers, sampling, and strict token budgets.
- Over‑blocking: start advisory; collect data; then enable gating.
- False positives in grounding: require explicit evidence pointers (hit ids) from the auditor.

## 13) Minimal Interfaces (Draft)
- Python signature
```python
def execute(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run deterministic audits; optionally call LLM auditor based on risk."""
```
- State writes
```python
meta["auditor"] = {
  "search": {"ok": bool, "issues": [...]},
  "redator": {"ok": bool, "issues": [...]},
  "professor": {"ok": bool, "issues": [...]},
  "pipeline": {"ok": bool, "elapsed_ms": int},
  "mode": "advisory|gate|retry_once",
  "elapsed_ms": int
}
```

---

This report is intended as a living document. We recommend starting with Phase 1 (deterministic checks, advisory mode) to gather telemetry, then incrementally enabling LLM auditing and gating based on observed issues and latency budgets.
