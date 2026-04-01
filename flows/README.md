# flows/

This directory reorganizes the first wave of migrated realtime code by **documentation flow step**, not by final package architecture.

Purpose:
- make the end-to-end live runtime flow visible in one place
- keep scripts/modules grouped under the numbered docs they primarily support
- make migration easier before the final source-tree layout is decided

Important:
- this is a **migration workspace**, not yet the final runtime package layout
- original files still exist in `trading-model` for now
- later we can consolidate these into a clean final `src/` layout inside `quantitative-trading`

---

## Flow index

### 01-overview
**Role:** top-level orientation layer for the live runtime system.

- status: documentation/navigation only
- local README: yes
- next likely work: keep as top-level orientation only; no need to turn it into a code bucket

### 02-runtime-and-modes
**Role:** long-running daemon state and runtime mode/event semantics.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - `daemon/`
  - `mode/`
  - `workflows/`

### 03-environment-and-operations
**Role:** startup, service management, runtime entrypoints, operational monitors.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - startup/service entrypoints
  - `scripts/entrypoints/`
  - `scripts/monitors/`

### 04-parameter-promotion-workflow-live
**Role:** active strategy pointer, promotion flow, upgrade request handling, unified upgrade event.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - `pointer/`
  - `promotion/`
  - `upgrade/`
  - `legacy-substeps/`

### 05-review-operations
**Role:** live review as execution-diagnostics and upgrade-validation output.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - `ingestion/`
  - `metrics/`
  - `reporting/`
  - `runners/`
  - `legacy-helpers/`

### 06-review-architecture
**Role:** architecture-only explanation layer.

- status: documentation only in this workspace
- code migrated: no dedicated flow directory

### 07-regime-and-decision-flow
**Role:** bridge between current market interpretation, active promoted inputs, and execution permission.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - `regime/`
  - `decision/`

### 08-state-and-artifacts
**Role:** persistent live state and the state/artifact boundary used by runtime and upgrades.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - `live-state/`
  - `position/`
  - `runtime-state/`
  - `legacy-models/`

### 09-execution-artifacts
**Role:** execution pipeline structure and artifact writer path.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - `pipeline/`
  - `policy/`
  - `verification/`
  - `exchange/`
  - `plumbing/`
  - `runners/`

### 10-research-runtime-separation-live
**Role:** live-only loops and helpers that must stay operationally independent from historical research.

- status: code migrated and secondarily reorganized
- local README: yes
- current structure:
  - `engines/`
  - `monitors/`
  - `notifications/`
  - `runtime-helpers/`

---

## Current maturity summary

### Documentation-only / navigation-heavy
- `01-overview`
- `06-review-architecture`

### Code migrated and secondarily reorganized by responsibility
- `02-runtime-and-modes`
- `03-environment-and-operations`
- `04-parameter-promotion-workflow-live`
- `05-review-operations`
- `07-regime-and-decision-flow`
- `08-state-and-artifacts`
- `09-execution-artifacts`
- `10-research-runtime-separation-live`

### Legacy-isolation already introduced
- `04-parameter-promotion-workflow-live/legacy-substeps/`
- `05-review-operations/legacy-helpers/`
- `08-state-and-artifacts/legacy-models/`

---

## Recommended next steps

1. decide whether `06` should remain docs-only or gain a matching code bucket
2. begin promoting stable subsets from `flows/` into a final `quantitative-trading/src/` layout
3. once the final layout exists, delete truly obsolete leftovers from the old repo with confidence
