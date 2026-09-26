---
title: 'Decision schema validation'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Triage decisions have no enforced contract, so downstream agent output could use unsupported categories, priorities, routes, or rationale text.

**Approach:** Add a reusable validation model for triage decisions that accepts only the Epic 1 values and rejects every other shape with a clear error.

</frozen-after-approval>

## Implementation Notes

Added `triage.schema.TriageDecision` with enum-backed category, priority, and route fields; category-to-route validation; forbidden extra fields; one-sentence rationale validation; and JSON/object validation through Pydantic. Added focused pytest coverage for valid output, unsupported values, route mismatches, all route mappings, rationale errors, abbreviations, extra fields, and JSON input. The review tightened sentence-boundary handling and required terminal punctuation.

## Review Triage Log

- **medium — patched:** Rationale validation accepted text without a sentence-ending boundary; terminal punctuation is now required and covered by a regression test.
- **medium — patched:** Periods in abbreviations such as `e.g.` could be mistaken for sentence boundaries; boundary detection now requires an uppercase or numeric next sentence token, with coverage for abbreviations.
- **low — patched:** Route validation tests did not cover every category mapping; the suite now parameterizes all five category-to-route pairs.
