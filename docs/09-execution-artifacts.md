# Execution Artifacts

Authoritative schema reference:
- `docs/12-runtime-data-contract.md`

## Purpose

Execution artifacts are the persistence boundary between:
- live runtime execution
- later review / upgrade validation
- operator debugging
- historical analysis of execution integrity

## Current artifact files

### Primary live-cycle artifacts
Written under:
- `logs/runtime/latest-execution-cycle.json`
- `logs/runtime/execution-cycles/YYYY-MM-DD.jsonl`

### Upgrade-event artifacts
Written under:
- `logs/runtime/latest-strategy-upgrade-request.json`
- `logs/runtime/latest-strategy-upgrade-result.json`
- `logs/runtime/latest-strategy-handover-marker.json`

## Writer entrypoints

Primary writer modules / entrypoints:
- `src/execution_cycle.py`
- `src/upgrade/process_strategy_upgrade_request.py`
- `src/runtime/workflows.py`

## Primary artifact model

The live system currently assumes one promoted live model/version and one active live execution path as the main operating model.

Each execution artifact should emphasize:

### 1. Raw execution-cycle payload
Built from `ExecutionCycleResult`.

### 2. Verification snapshot
Stored under:
- `verification_snapshot`

This records execution verification quality such as:
- verification attempts
- trade confirmation hints
- local position status
- reconcile-related diagnostics

### 3. Attribution snapshot
Stored under:
- `attribution_snapshot`

This bridges execution into review/accounting with fields such as:
- `execution_id`
- `client_order_id`
- `order_id`
- `trade_ids`
- fee / realized / equity provenance hints

### 4. Theoretical snapshot
Stored under:
- `theoretical_snapshot`

This captures the intended live-side trading decision and the first-pass theoretical-vs-actual comparison anchors, such as:
- intended action / side / size / reason
- plan score / theoretical strength
- expected notional proxy
- theoretical gross pnl proxy (when realized pnl / fee / funding fields exist)
- execution drag proxy

These fields are expected to be sparse during hold-only / dry-run cycles and become meaningful once cycles include actual fills / fees / pnl observations.

### 5. Summary layer
Stored under:
- `result.summary`

Current policy:
- keep the summary layer leaner than before, but **do not prematurely strip potentially valuable report/stat fields**
- retain statistics that may become first-class report/dashboard inputs even if the current report pipeline is not fully exploiting them yet
- remove pure mirror layers at the artifact top level when they add no information

Examples of currently valuable summary data to preserve:
- active strategy identity / promotion metadata
- verification counters
- theoretical-vs-actual execution deviation fields
- attribution provenance fields
- ledger/position bookkeeping fields useful for execution diagnostics
- strategy stats eligibility / anomaly reason fields

### 6. Upgrade handover metadata
Where relevant, upgrade-time artifacts should surface:
- open-position observation
- handover policy
- handover decision
- handover marker reference

## Canonical direction

### Canonical enough today
- live execution artifact file locations
- execution summary / verification fields
- active strategy metadata tagging
- upgrade request/result/handover marker artifact family
- slimmer top-level artifact structure for `latest-execution-cycle.json`

### Remove over time
- broken compare/debug semantics that only existed for the former router-composite path
- dead modules that reference no-longer-existent structures
- field names or payload shapes tied to now-removed multi-account assumptions
- pure mirror layers that add no analytical or operational value

## Operator usage

Use execution-cycle artifacts when:
- diagnosing the latest live execution path
- checking verification / reconcile details
- inspecting which active strategy version was running
- preserving raw material for future reporting/dashboard iterations

Use upgrade request/result artifacts when:
- validating a promotion-triggered strategy upgrade
- auditing handover policy and decision when positions were open
- diagnosing post-upgrade behavior

## Main code / script touchpoints

- `src/execution/pipeline.py`
- `src/execution_cycle.py`
- `src/upgrade/strategy_pointer.py`
- `src/upgrade/process_strategy_upgrade_request.py`
- `src/runtime/workflows.py`
- `src/state/store.py`
- `src/state/live_position.py`
