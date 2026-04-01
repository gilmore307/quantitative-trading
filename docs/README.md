# quantitative-trading docs

This docs tree is the canonical home for realtime trading / live execution / runtime operations documentation.

## Start here

- `runtime-and-modes.md`
- `execution-artifacts.md`
- `review-operations.md`
- `review-architecture.md`
- `environment-and-operations.md`
- `state-and-artifacts.md`
- `parameter-promotion-workflow-live.md`
- `research-runtime-separation-live.md`

## Core operating model

- trade daemon is the continuous live-running state
- historical research promotes new strategy / parameter / trading-instruction versions
- trade daemon detects active strategy changes without restarting
- `strategy_upgrade_event` is the canonical promotion-triggered validation/helper event
- one live account is the current intended operating model
- live review focuses on execution fidelity and execution-system health, not direct model optimization

## Realtime architecture / operations

- `runtime-and-modes.md`
- `execution-artifacts.md`
- `environment-and-operations.md`
- `state-and-artifacts.md`
- `regime-and-decision-flow.md`

## Live review / promotion / workflow

- `review-operations.md`
- `review-architecture.md`
- `parameter-promotion-workflow-live.md`
- `research-runtime-separation-live.md`

## Documentation rule for this repo

Each substantive realtime doc should explicitly list the main code / script touchpoints it depends on.
That mapping is the source of truth for later script/module migration.

## Historical note

These docs were migrated out of the former hybrid `crypto-trading` / `trading-model` repo so realtime trading content can live in its own repository.
