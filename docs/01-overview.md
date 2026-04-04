# 01 Overview

This document is the top-level introduction to the `trading-execution` live runtime flow.

The goal is to make the whole realtime system readable in one pass before diving into detailed docs.

## System role

`trading-execution` is the live execution repository.

It is responsible for:
- continuously running the trade daemon
- reading the current promoted live strategy / trading-instruction pointer
- executing live trades
- recording execution artifacts
- detecting strategy upgrades without restarting the daemon
- running upgrade validation out-of-band

It is **not** the place where model optimization happens.
Model optimization belongs to the historical research / backtest side.

## Two-line relationship

### Historical line
Historical research / backtest is responsible for:
- extending data
- adding new symbols / variants / families
- ranking / selection / retune / archive
- deciding promotion

### Live line
Realtime trading is responsible for:
- consuming the promoted result
- trading continuously with the **single currently promoted live model/version**
- loading the required external runtime input bundle (label parameters, strategy parameters, and label-to-strategy mapping)
- recording real execution behavior
- diagnosing execution deviations and operational health

Important constraint:
- this repo is **not** intended to keep a standing matrix of live family accounts all trading in parallel
- family labels from the historical side are selection / taxonomy outputs, not the steady-state live execution roster
- the canonical live object is the currently promoted active strategy/model pointer
- runtime must fail closed when the external model-input bundle is missing; no hidden default label/strategy model should continue trading

## Main flow

### Step 1 — historical side promotes a new live version
A promoted strategy / parameter / trading-instruction version is produced outside this repo.

See:
- `04-parameter-promotion-workflow-live.md`

### Step 2 — active strategy pointer is updated
The live runtime reads a canonical active pointer that tells the daemon what the current promoted live version is.

See:
- `02-runtime-and-modes.md`
- `08-state-and-artifacts.md`

### Step 3 — trade daemon keeps running
The trade daemon is the continuous runtime state.
It should not stop just because review or upgrade-related work happens.

See:
- `02-runtime-and-modes.md`
- `03-environment-and-operations.md`

### Step 4 — daemon detects version change
When the active strategy pointer changes, the daemon detects the new active version without restart.

See:
- `02-runtime-and-modes.md`
- `07-regime-and-decision-flow.md`

### Step 5 — daemon continues trading and emits upgrade request
The daemon continues trading with the new version and emits a `strategy_upgrade_event_requested` request artifact for out-of-band handling.

See:
- `04-parameter-promotion-workflow-live.md`
- `05-review-operations.md`
- `06-review-architecture.md`

### Step 6 — out-of-band upgrade validation runs
A separate consumer processes the request and runs the unified `strategy_upgrade_event`.
This event now centers on handover recording plus review, and no longer performs calibrate/reset actions by default.

See:
- `02-runtime-and-modes.md`
- `05-review-operations.md`
- `06-review-architecture.md`

### Step 7 — execution / upgrade artifacts become review inputs
Execution artifacts, upgrade request/result artifacts, and handover markers become the audit trail for the live system.

See:
- `08-state-and-artifacts.md`
- `09-execution-artifacts.md`

## Position handling rule during upgrade

If the active strategy changes while a position is open:
- do not force a special upgrade-only flatten
- reuse normal strategy-switch / ownership-transition handling
- record handover observation / decision / marker

See:
- `05-review-operations.md`
- `06-review-architecture.md`
- `08-state-and-artifacts.md`

## Review role

Realtime review is not the main model-optimization loop.
Its main job is to answer:
- was the promoted live strategy executed faithfully?
- where did execution deviate from theory?
- is the execution system healthy?

See:
- `05-review-operations.md`
- `06-review-architecture.md`
- `10-research-runtime-separation-live.md`

## Recommended reading order

1. `01-overview.md`
2. `02-runtime-and-modes.md`
3. `03-environment-and-operations.md`
4. `04-parameter-promotion-workflow-live.md`
5. `05-review-operations.md`
6. `06-review-architecture.md`
7. `07-regime-and-decision-flow.md`
8. `08-state-and-artifacts.md`
9. `09-execution-artifacts.md`
10. `10-research-runtime-separation-live.md`
