# 05 Review Operations

This flow step covers realtime review as execution-diagnostics and upgrade-validation output.

## Responsibility

- read runtime execution history
- build review metrics / sections / summaries
- export JSON/Markdown review artifacts
- support upgrade-triggered review and any remaining low-frequency health reviews

## Current contents

- `src/runners/weekly_review.py`
- `src/runners/monthly_review.py`
- `src/runners/quarterly_review.py`
- `src/review/`

## Likely next additions

- review wrappers more tightly aligned with `strategy_upgrade_event`
- any remaining live-review-only helpers still outside `src/review/`

## Expected future home

These files will likely live under final `src/review/` and `src/runners/` locations in `quantitative-trading`.
