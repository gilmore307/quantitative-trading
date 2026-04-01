# flows/

This directory reorganizes the first wave of migrated realtime code by **documentation flow step**, not by final package architecture.

Purpose:
- make the end-to-end live runtime flow visible in one place
- keep scripts/modules grouped under the numbered docs they primarily support
- make migration easier before the final source-tree layout is decided

Current interpretation:
- `02-runtime-and-modes/` — long-running trade daemon and runtime mode/event semantics
- `04-parameter-promotion-workflow-live/` — active strategy pointer, promotion, upgrade request/consumer, unified upgrade event
- `05-review-operations/` — live review/report runners and review pipeline code
- `08-state-and-artifacts/` — state, live position, runtime log/state helpers
- `09-execution-artifacts/` — execution pipeline and execution artifact writer path

Important:
- this is a **migration workspace**, not yet the final runtime package layout
- original files still exist in `trading-model` for now
- later we can consolidate these into a clean final `src/` layout inside `quantitative-trading`
