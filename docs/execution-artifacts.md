# Execution Artifacts

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
- `src/runners/execution_cycle.py`
- `src/runners/process_strategy_upgrade_request.py`
- `src/runners/strategy_upgrade_event.py`

## Primary artifact model

The live system currently assumes one live account as the main operating model.

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

### 4. Active strategy metadata
Stored under summary/artifact metadata, including fields such as:
- `active_strategy_version`
- `active_strategy_source`
- `active_strategy_family`
- `active_strategy_config_path`
- `active_strategy_promoted_at`
- `active_strategy_promotion_note`

### 5. Upgrade handover metadata
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

### Old hybrid-repo leftovers to remove over time
- compare/debug semantics that only existed for the former router-composite path
- field names or payload shapes tied to now-removed multi-account assumptions

## Operator usage

Use execution-cycle artifacts when:
- diagnosing the latest live execution path
- checking verification / reconcile details
- inspecting which active strategy version was running

Use upgrade request/result artifacts when:
- validating a promotion-triggered strategy upgrade
- auditing handover policy and decision when positions were open
- diagnosing post-upgrade behavior

## Main code / script touchpoints

- `src/execution/pipeline.py`
- `src/runners/execution_cycle.py`
- `src/runtime/strategy_pointer.py`
- `src/runners/process_strategy_upgrade_request.py`
- `src/runners/strategy_upgrade_event.py`
- `src/state/store.py`
- `src/state/live_position.py`
