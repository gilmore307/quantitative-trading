# trading-execution docs

This docs tree is the canonical home for realtime trading / live execution / runtime operations documentation.

## Read in order

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

## Core operating model

- trade daemon is the continuous live-running state
- historical research promotes new strategy / parameter / trading-instruction versions
- trade daemon detects active strategy changes without restarting
- `strategy_upgrade_event` is the canonical promotion-triggered validation/helper event
- one live account is the current intended operating model
- live review focuses on execution fidelity and execution-system health, not direct model optimization

## Documentation rule for this repo

Each substantive realtime doc should explicitly list the main code / script touchpoints it depends on.
That mapping is the source of truth for later script/module migration.
