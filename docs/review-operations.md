# Review Operations

This document describes the review path for the live trading system.

## New primary framing

Realtime review is no longer the place where model optimization happens.

Historical research is responsible for:
- ranking
- selection
- retune
- promotion / archive
- family / variant / parameter optimization

Realtime review is responsible for:
- validating execution fidelity
- diagnosing execution deviations
- checking execution-system health
- producing clues that may later be investigated on the historical-research side

In short:
- historical line optimizes the model
- realtime line verifies execution and operational health

## Main review question

Realtime review should no longer primarily ask:
- "is this strategy good?"

It should ask:
- "was the current strategy executed correctly and faithfully?"

## Canonical review trigger

The primary review trigger is now:
- **promotion-triggered strategy upgrade**

Not:
- weekly ritual by default

The most important review moment is when a promoted strategy / parameter version becomes active in live trading.

## Strategy-upgrade review

The canonical live review path is now the unified strategy-upgrade event.

Primary intent:
- validate the effect of a newly promoted strategy / parameter version
- review theoretical-signal vs actual-execution deviations
- review execution quality, position drift, and operational anomalies
- keep trading running while validation is generated

Run the unified strategy-upgrade event runner:

```bash
./.venv/bin/python -m src.runners.strategy_upgrade_event
```

Optional helper cleanup:

```bash
./.venv/bin/python -m src.runners.strategy_upgrade_event --destructive
```

## Trade and review relationship

### Trade daemon
- long-running
- always on
- keeps reading the latest active strategy pointer
- does not stop because of review
- does not stop because of calibration/helper work

### Review path
- out-of-band
- read-oriented
- triggered mainly by promotion / upgrade events
- does not control the trade daemon’s main loop

## Position handling during strategy upgrade

If a live position exists when the active strategy version changes, do not stop the daemon just to make the upgrade look clean.

Use strategy-switch handling instead:
- keep trade running on the new active version immediately
- reuse normal ownership-transition / switch semantics
- if the new active strategy should keep the position, continue under the new context
- if the new active strategy should close-and-wait, let the normal execution/switch path unwind it
- record the upgrade request even when a position is open

## Core review outputs

A realtime review should emphasize:

### A. Signal fidelity
- theoretical signal timestamp
- actual order timestamp
- signal-to-order delay
- missed signals
- duplicated executions
- stale signal execution

### B. Position fidelity
- theoretical position
- actual position
- position drift
- drift duration
- reconciliation status

### C. Execution health
- order submit success rate
- rejects / cancels / timeouts
- partial fills
- broker / exchange errors
- data lag / feed anomalies

### D. Deviation diagnostics
- latency
- missed order
- duplicate order
- manual override
- exchange reject
- partial fill
- state desync
- stale data
- reconciliation gap

### E. Actionable execution improvements
- routing improvements
- reconcile improvements
- signal/order coupling improvements
- retry / protection logic improvements

## What live review should not directly do

Realtime review should not be the primary place for:
- family promotion/demotion
- variant淘汰 /淘汰 decisions
- parameter retuning
- cluster ranking recomputation
- direct model updates

Those belong to the historical research line.

## Secondary scheduled reviews

Low-frequency scheduled health reviews may still exist.
But they should be treated as secondary health checks, not the main review architecture.

The main review architecture is:
- promotion-triggered
- upgrade-validation oriented
- execution-diagnostics first

## Main code / script touchpoints

### Upgrade-triggered review entrypoints
- `src/runners/strategy_upgrade_event.py`
- `src/runners/process_strategy_upgrade_request.py`
- `src/runtime/workflows.py`

### Review pipeline
- `src/review/ingestion.py`
- `src/review/aggregator.py`
- `src/review/performance.py`
- `src/review/report.py`
- `src/review/export.py`

### Review runners / scripts
- `src/runners/review_event.py`
- `src/runners/weekly_review.py`
- `src/runners/monthly_review.py`
- `src/runners/quarterly_review.py`
- `scripts/review/weekly_review.py`
- `scripts/review/monthly_review.py`
- `scripts/review/quarterly_review.py`

### Runtime artifacts consumed by review
- `src/runners/execution_cycle.py`
- `src/execution/pipeline.py`
- `src/runtime/strategy_pointer.py`
- `src/state/store.py`
