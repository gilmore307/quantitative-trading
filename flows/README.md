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
- code migrated: no
- local README: yes
- next likely work: keep as top-level orientation only; no need to turn it into a code bucket

### 02-runtime-and-modes
**Role:** long-running daemon state and runtime mode/event semantics.

- status: code migrated
- code shape: still shallow; not yet secondarily reorganized beyond initial grouping
- local README: yes
- current key contents:
  - `trade_daemon.py`
  - runtime mode / policy / workflow files
- next likely work:
  - decide whether to split this further into `daemon/`, `mode/`, and `workflow/`

### 03-environment-and-operations
**Role:** startup, service management, runtime entrypoints, operational monitors.

- status: code migrated and secondarily reorganized
- local README: yes
- current key contents:
  - startup/service entrypoints
  - `entrypoints/`
  - `monitors/`
- cleanup already done:
  - old `crypto-trading` working-directory paths removed from migrated daemon/service wrappers
- next likely work:
  - migrate more live runtime shell/service helpers if still needed

### 04-parameter-promotion-workflow-live
**Role:** active strategy pointer, promotion flow, upgrade request handling, unified upgrade event.

- status: code migrated and secondarily reorganized
- local README: yes
- current key contents:
  - `pointer/`
  - `promotion/`
  - `upgrade/`
  - `legacy-substeps/`
- cleanup already done:
  - old `crypto-trading` runtime log paths removed from migrated pointer/request scripts
- next likely work:
  - dedupe/idempotency helpers
  - stronger pointer schema/validation

### 05-review-operations
**Role:** live review as execution-diagnostics and upgrade-validation output.

- status: code migrated and secondarily reorganized
- local README: yes
- current key contents:
  - `ingestion/`
  - `metrics/`
  - `reporting/`
  - `runners/`
  - `legacy-helpers/`
- cleanup already done:
  - isolated `compare.py` from the main review path as an older comparison-oriented helper
- next likely work:
  - align runners more tightly with upgrade-triggered review rather than cadence-first review

### 06-review-architecture
**Role:** currently represented mainly by docs, not a separate code bucket.

- status: documentation only in this workspace
- code migrated: no dedicated flow directory yet
- next likely work:
  - decide whether a separate architecture-only flow directory is useful, or keep this as docs-only

### 07-regime-and-decision-flow
**Role:** bridge between current market interpretation, active promoted inputs, and execution permission.

- status: code migrated
- local README: yes
- current key contents:
  - `regime_runner.py`
  - decision/policy helpers
- next likely work:
  - determine whether more decision-trace logic should move here from execution pipeline

### 08-state-and-artifacts
**Role:** persistent live state and the state/artifact boundary used by runtime and upgrades.

- status: code migrated and secondarily reorganized
- local README: yes
- current key contents:
  - `live-state/`
  - `position/`
  - `runtime-state/`
  - `legacy-models/`
- cleanup already done:
  - isolated old unreferenced `models.py` into `legacy-models/`
- next likely work:
  - extract handover-marker helpers if needed
  - continue separating true live-state code from historical leftovers

### 09-execution-artifacts
**Role:** execution pipeline structure and artifact writer path.

- status: code migrated and secondarily reorganized
- local README: yes
- current key contents:
  - `pipeline/`
  - `policy/`
  - `verification/`
  - `exchange/`
  - `plumbing/`
  - `runners/`
- next likely work:
  - extract artifact-schema helpers if they deserve a dedicated layer

### 10-research-runtime-separation-live
**Role:** live-only loops and helpers that must remain operationally independent from historical research.

- status: code migrated
- local README: yes
- current key contents:
  - live runtime helper runners
  - notifier / watcher helpers
  - runtime-side time/bucket helpers
- next likely work:
  - decide whether to split further into `watchers/`, `notifications/`, and `runtime-helpers/`

---

## Current maturity summary

### Documentation-only / navigation-heavy
- `01-overview`
- `06-review-architecture`

### Code migrated but not yet deeply reorganized
- `02-runtime-and-modes`
- `07-regime-and-decision-flow`
- `10-research-runtime-separation-live`

### Code migrated and secondarily reorganized by responsibility
- `03-environment-and-operations`
- `04-parameter-promotion-workflow-live`
- `05-review-operations`
- `08-state-and-artifacts`
- `09-execution-artifacts`

### Legacy-isolation already introduced
- `04-parameter-promotion-workflow-live/legacy-substeps/`
- `05-review-operations/legacy-helpers/`
- `08-state-and-artifacts/legacy-models/`

---

## Recommended next steps

1. finish second-level reorganization for `02`, `07`, and `10`
2. decide whether `06` should remain docs-only or gain a matching code bucket
3. once flows are stable, begin promoting stable subsets into a final `quantitative-trading/src/` layout
4. only after that, delete truly obsolete leftovers from the old repo with confidence
