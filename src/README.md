# src/

This is the beginning of the final source layout for `quantitative-trading`.

Current status:
- `src/` is the authoritative live codebase for `quantitative-trading`
- the old `flows/` migration workspace has been retired to avoid split-brain maintenance and confusion

## Current package skeleton

### `src/runtime/`
Live daemon/runtime semantics:
- trade daemon
- mode / mode policy
- workflow / workflows
- runtime helpers such as business time and bucket state
- runtime-side regime runner / live decision input bridge

Current terminology note:
- regime labels such as `trend`, `range`, `compression`, `crowded`, and `shock` are execution-decision / market-state categories
- they are **not** separate live accounts or separate live strategy families in the current architecture
- live trading routes through the single `active_live` execution path

### `src/upgrade/`
Promotion-time live runtime handling:
- active strategy pointer
- promotion entrypoint
- strategy upgrade request processing
- unified strategy upgrade event

### `src/execution/`
Live execution pipeline components:
- pipeline/controller
- policy
- confirmation
- exchange snapshot / adapters
- identifiers / locks
- temporary decision-bridge helpers absorbed from the old `07` flow

### `src/review/`
Live review / upgrade-validation pipeline:
- ingestion/history loading
- metrics / aggregation / performance
- report building
- export

### `src/state/`
Live state support:
- state store
- live positions
- state/runtime log paths

### `src/ops/`
Live runtime operational helpers:
- monitors
- alert watchers
- notifications

## Authority rule

`src/` is the only authoritative runtime code path for this repository.
Do not maintain duplicate runtime logic under parallel directory trees.

## Validation rule

Before deleting old or duplicated scripts/modules, run the planned end-to-end dummy-strategy test path.
That pass was used to confirm the surviving live path before retiring the old `flows/` tree.
