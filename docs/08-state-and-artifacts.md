# State and Artifacts

This document summarizes the main runtime state files and artifact families used by `quantitative-trading`.

## Current principle

Authoritative schema reference:
- `docs/12-runtime-data-contract.md`

This project should act as a durable **runtime data producer**.

That means:
- preserve structured runtime records that future dashboard/report consumers can rely on
- keep artifact schemas stable and explicit
- remove broken migration leftovers and dead compatibility paths
- avoid prematurely thinning potentially valuable statistics before downstream consumers are finalized

## Main runtime state files

### Active strategy pointer
- `logs/runtime/active-strategy.json`

Purpose:
- current promoted strategy/model version for live execution
- promotion metadata such as family, source, config path, promotion note

### Active model inputs
- `logs/runtime/active-model-inputs.json`

Purpose:
- runtime label thresholds / model-input bundle required by the regime runner
- should be treated as required runtime input data, not a temporary convenience file

### Runtime mode / daemon state
- `logs/runtime/trade-daemon.pid`
- `logs/runtime/trade-daemon.lock`
- `logs/runtime/strategy-upgrade-state.json`
- `logs/runtime/route-registry.json`

Purpose:
- daemon singleton / lifecycle bookkeeping
- durable last-seen strategy version state for upgrade detection
- route registry state

## Main artifact families

### Latest active execution artifact
- `logs/runtime/latest-execution-cycle.json`

Current top-level structure:
- `artifact_type`
- `recorded_at`
- `runtime_state`
- `active_strategy`
- `result`
- `live_positions`

Canonical rule:
- top level should remain slim
- detailed execution statistics should primarily live under `result.summary` and companion snapshots

### Historical execution stream
- `logs/runtime/execution-cycles/YYYY-MM-DD.jsonl`

Purpose:
- append-only active execution history
- intended as a durable source for future dashboard/report consumers

### Detailed execution history
- `logs/runtime/execution-cycle-details/YYYY-MM-DD.jsonl`

Purpose:
- full richer execution artifact history
- useful when dashboard/report layers need deeper raw fields than the lighter history stream

### Regime-local history
- `logs/runtime/regime-local-history/YYYY-MM-DD.jsonl`

Purpose:
- regime/route oriented local summary stream
- useful for later dashboard slicing by regime / route / active strategy

### Execution anomalies
- `logs/runtime/execution-anomalies/YYYY-MM-DD.jsonl`

Purpose:
- isolated anomaly / non-clean-execution records
- supports later dashboarding around operational health and reconciliation quality

### Strategy upgrade artifacts
- `logs/runtime/latest-strategy-upgrade-request.json`
- `logs/runtime/latest-strategy-upgrade-result.json`
- `logs/runtime/latest-strategy-handover-marker.json`

Purpose:
- durable upgrade-event request/result tracking
- handover audit trail when active strategy version changes

## Schema expectations for future dashboard consumers

Future dashboard/report consumers should assume:
- active execution artifacts live under `result.summary` + snapshot subtrees
- `latest-execution-cycle.json` no longer exposes a top-level mirror `summary`
- old `summary.primary_summary` compatibility shape is not canonical anymore
- route, attribution, theoretical, verification, and bookkeeping statistics are intentionally retained when they may be analytically useful later

## What should continue to be removed

- old repo-path references to `crypto-trading`
- dead `src/runners/*` path references when the real implementation already lives under `src/runtime/`, `src/upgrade/`, or `src/execution_cycle.py`
- broken compatibility code that references no-longer-existent structures
- stale compare/router-composite era leftovers that are no longer part of the single-active-strategy architecture
