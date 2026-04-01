# 05 Review Operations

This flow step covers realtime review as execution-diagnostics and upgrade-validation output.

## Responsibility

- read runtime execution history
- build review metrics / sections / summaries
- export JSON/Markdown review artifacts
- support upgrade-triggered review and any remaining low-frequency health reviews

## Current contents

### ingestion
- `ingestion/ingestion.py`
- `ingestion/history_loader.py`

### metrics
- `metrics/account_metrics.py`
- `metrics/aggregator.py`
- `metrics/performance.py`
- `metrics/framework.py`

### reporting
- `reporting/report.py`
- `reporting/export.py`

### runners
- `runners/weekly_review.py`
- `runners/monthly_review.py`
- `runners/quarterly_review.py`

### legacy-helpers
- `legacy-helpers/compare.py`

## Notes on current cleanup

`compare.py` is intentionally isolated from the main review flow because it appears to belong to older comparison-oriented review logic rather than the current execution-fidelity-first review path.

## Likely next additions

- upgrade-review wrappers more tightly aligned with `strategy_upgrade_event`
- any remaining live-review-only helpers still outside this flow step

## Expected future home

These files will likely live under final review/report packages and selected runner entrypoints inside `quantitative-trading`.
