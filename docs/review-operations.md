# Review Operations

This document is the operator/runbook entry for the review pipeline.

## Current scope

The project now has a first usable review artifact pipeline with:

- canonical performance ingestion from execution artifacts
- execution-history aggregation
- weekly/monthly/quarterly review report generation
- JSON + Markdown export under `reports/trade-review/`

Current operating assumption:

- live trading runs one real account on the latest promoted strategy version
- the trade daemon is a separate long-running process and should keep running during review generation
- live review is for execution + realized-result diagnostics
- live review is not the primary parameter-optimization loop

## Primary artifact source

Execution history is read from:

- `logs/runtime/execution-cycles/YYYY-MM-DD.jsonl` business-timezone daily partitions in `America/New_York`

Review reports are written to:

- `reports/trade-review/`

Convenience files maintained automatically:

- `latest_weekly.json` / `latest_weekly.md`
- `latest_monthly.json` / `latest_monthly.md`
- `latest_quarterly.json` / `latest_quarterly.md`
- `index.json` — rolling report index with latest-by-cadence pointers

## Strategy-upgrade review

This is now the canonical live-operations review trigger.

Primary intent:
- validate the effect of a newly promoted strategy / parameter version
- review theoretical-signal vs actual-execution deviations
- review execution quality, position drift, and operational anomalies
- keep trading running while validation is generated; the review is attached to the same promotion-triggered strategy upgrade event and does not force daemon mode switches

Run the unified strategy-upgrade event runner:

```bash
./.venv/bin/python -m src.runners.strategy_upgrade_event
```

Optional helper cleanup:

```bash
./.venv/bin/python -m src.runners.strategy_upgrade_event --destructive
```

## Position handling during strategy upgrade

If a live position exists when the active strategy version changes, do not stop the daemon just to "make the upgrade clean".

Use strategy-switch handling instead:

- keep trade running on the new active version immediately
- treat any existing live position under the same logic used for strategy switching / ownership transition
- if the new active strategy wants to keep/own the position, continue managing it under the new strategy context
- if the new active strategy wants to close-and-wait, let the normal execution/switch path unwind it rather than forcing a separate upgrade-time stopout
- record the upgrade request even when a position is open; open position is not a blocker for the strategy-upgrade event

## Monthly review

This is an aggregate live-operations summary, not the main parameter-discussion layer.

## Quarterly review

This is a structural live-operations / execution-system review layer.

## Output contents

Each review export produces:

- one JSON artifact
- one Markdown artifact

The report currently contains:

- executive summary
- recommended actions
- realized live-performance summary
- execution-quality / deviation sections
- section status summary

## Operator note

`review` and `calibrate` should be understood as event/helper concepts, not daemon runtime modes.

Use the unified `strategy_upgrade_event` as the primary operator entry when a new promoted strategy version is adopted in live trading.
