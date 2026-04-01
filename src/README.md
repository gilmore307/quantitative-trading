# src/

This is the beginning of the final source layout for `quantitative-trading`.

Current status:
- `flows/` remains the migration workspace and process-oriented reorganization layer
- `src/` is where stabilized realtime code starts being promoted into its long-term package layout

## Current package skeleton

### `src/runtime/`
Live daemon/runtime semantics:
- trade daemon
- mode / mode policy
- workflow / workflows
- runtime helpers such as business time and bucket state

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

## Migration rule

Code should only be promoted from `flows/` into `src/` after:
- its role is clear under the current design philosophy
- its place in the live runtime flow is stable enough
- we are comfortable treating it as part of the final package structure

## Validation rule

Before deleting old or duplicated scripts/modules, run the planned end-to-end dummy-strategy test path.
That pass will help reveal which files still matter and which can be removed safely.
