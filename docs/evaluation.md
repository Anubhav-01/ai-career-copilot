# AI Evaluation

The repo ships a small evaluation harness for the deterministic AI components:

```bash
cd apps/api
python -m evals.run
```

## What is measured

| Component | Metric | Dataset |
|---|---|---|
| Skill extraction | precision / recall / F1 | `evals/data/labeled_skills.json` (10 labeled snippets incl. negatives and trap cases like "reactive" ≠ react) |
| Resume extraction | per-field accuracy (email, phone, sections, skills) | `evals/data/labeled_resumes.json` (3 synthetic resumes, 12 field checks) |
| Matching / similarity quality | ranking sanity: related job must outrank an unrelated job for the same resume | inline synthetic pair |

The harness exits non-zero if skill F1 < 0.8, extraction accuracy < 0.9, or the
ranking check fails — so it can be wired into CI as a regression gate.

## Current results (local run)

```
[1] Skill extraction (10 cases)      precision=1.0  recall=1.0  f1=1.0
[2] Resume extraction (12 checks)    accuracy=1.0
[3] Matching sanity (hashing)        related=0.21 > unrelated=0.08  ✓
```

## Honest limitations — read before quoting numbers

- **The datasets are small and synthetic**, and were written by the same
  authors as the taxonomy. Perfect scores here mean "no regressions against
  the covered cases", **not** production accuracy. Real resumes (creative
  layouts, tables, multi-column PDFs, non-English) will score lower.
- **Skill extraction recall is bounded by the taxonomy** (~150 canonical
  skills). Skills outside it are invisible by design (a deliberate
  anti-hallucination trade-off).
- **The ranking check uses the fallback hashing embedder** when ML extras are
  not installed; it verifies the pipeline's ordering behavior, not
  sentence-transformer quality. With `requirements-ml.txt` installed, the same
  harness exercises the real model.
- **LLM-dependent outputs** (refinement quality, interview feedback quality,
  roadmap usefulness) are *not* auto-scored. Unit tests verify schema
  compliance and grounding behavior with the mock provider; judging real-LLM
  output quality requires a human-reviewed set. A practical next step: collect
  ~30 answer/feedback pairs, have two reviewers rate them 1–5 on usefulness and
  factuality, and track agreement over prompt changes.
- Interview feedback is intentionally evaluated on **text only**; no claims are
  made about confidence, personality or psychology.

## Extending

- Add cases to the JSON files (they are plain labeled examples).
- `evals/run.py` is dependency-light and importable — each `eval_*` function
  returns a dict, so new metrics can be added and asserted in CI.
