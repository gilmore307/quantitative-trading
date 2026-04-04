# 12 Runtime Data Contract

This document records the current runtime artifact contract for `trading-execution`.

Purpose:
- provide one stable reference for future dashboard/report consumers
- make the current artifact shape explicit
- distinguish stable producer outputs from historical compatibility leftovers
- reduce ambiguity when new downstream readers are added later

## Contract intent

`trading-execution` should behave as a **runtime data producer**.

That means:
- artifact files should be stable and explicit
- potentially valuable runtime statistics should be preserved unless clearly redundant or broken
- downstream consumers (dashboard/report/audit tools) should read from these artifacts rather than depending on internal in-memory structures
- broken migration leftovers should be removed instead of preserved as pseudo-API

## Current primary artifact files

### Latest active execution artifact
- `logs/runtime/latest-execution-cycle.json`

Purpose:
- latest active execution cycle snapshot
- best single-file source for “what just happened”

### Historical active execution stream
- `logs/runtime/execution-cycles/YYYY-MM-DD.jsonl`

Purpose:
- append-only active execution cycle history
- main durable history stream for downstream analytics

### Detailed execution history
- `logs/runtime/execution-cycle-details/YYYY-MM-DD.jsonl`

Purpose:
- fuller detailed execution artifacts for deeper forensic/debug usage

### Regime-local history
- `logs/runtime/regime-local-history/YYYY-MM-DD.jsonl`

Purpose:
- lighter regime/route oriented history stream

### Execution anomalies
- `logs/runtime/execution-anomalies/YYYY-MM-DD.jsonl`

Purpose:
- anomaly-focused subset for degraded/non-clean execution analysis

### Strategy-upgrade artifacts
- `logs/runtime/latest-strategy-upgrade-request.json`
- `logs/runtime/latest-strategy-upgrade-result.json`
- `logs/runtime/latest-strategy-handover-marker.json`

Purpose:
- durable upgrade request/result/handover audit trail

## Current canonical shape of `latest-execution-cycle.json`

Top-level keys currently expected:
- `artifact_type`
- `recorded_at`
- `runtime_state`
- `active_strategy`
- `result`
- `live_positions`

Important rule:
- **top-level mirror summary fields are no longer canonical**
- consumers should primarily read execution statistics from `result.summary`
- old compatibility assumptions such as top-level `summary.primary_summary` should not be used by new consumers

## Top-level field meanings

### `artifact_type`
Expected value:
- `active_strategy_execution_cycle`

### `recorded_at`
- ISO timestamp for artifact write time

### `runtime_state`
Purpose:
- current runtime mode and related runtime-state fields at artifact write time

### `active_strategy`
Purpose:
- full active strategy pointer snapshot at execution time
- includes version/source/metadata as written by the promotion system

### `result`
Purpose:
- canonical execution-cycle artifact payload
- this is where most future consumers should read structured execution statistics

### `live_positions`
Purpose:
- current live position snapshot carried alongside the active execution artifact

## Canonical shape of `result`

`result` is an execution artifact with the following important subtrees:
- `summary`
- `feature_snapshot`
- `theoretical_snapshot`
- `verification_snapshot`
- `attribution_snapshot`
- `ledger_snapshot`

The full raw execution payload may also include other execution-cycle fields inherited from `ExecutionCycleResult`, but downstream consumers should prefer the explicitly curated subtrees above where possible.

## `result.summary` contract

`result.summary` is the current **canonical summary layer**.

Design goals:
- compact enough for common consumers
- rich enough to preserve potentially valuable runtime statistics for future dashboard/report work
- not forced to be minimal if that would throw away useful analytical signal

### Current field groups inside `result.summary`

#### Identity / execution ids
Examples:
- `symbol`
- `execution_id`
- `client_order_id`
- `order_id`
- `trade_ids`

#### Verification metrics
Examples:
- `entry_verified_hint`
- `entry_trade_confirmed`
- `entry_verification_attempt_count`
- `entry_trade_confirmed_attempt_count`

#### Theoretical-vs-actual metrics
Examples:
- `theoretical_action`
- `theoretical_side`
- `theoretical_size`
- `theoretical_reason`
- `theoretical_score`
- `theoretical_strength`
- `theoretical_gross_pnl_proxy_usdt`
- `execution_drag_proxy_usdt`

#### Ledger / position bookkeeping
Examples:
- `open_leg_count`
- `closed_leg_count`
- `pending_exit_leg_count`
- `ledger_open_size`
- `position_size`
- `position_ledger_diff`
- `live_position_count`
- `position_open_during_cycle`

#### Runtime / active strategy metadata
Examples:
- `runtime_mode`
- `active_strategy_version`
- `active_strategy_updated_at`
- `active_strategy_source`
- `active_strategy_label`
- `active_strategy_config_path`
- `active_strategy_promoted_at`
- `active_strategy_promotion_note`

#### Decision / route / submission state
Examples:
- `regime`
- `confidence`
- `plan_action`
- `plan_account`
- `plan_reason`
- `active_route`
- `route_account`
- `route_trade_enabled`
- `trade_enabled`
- `pipeline_entered`
- `submission_allowed`
- `submission_attempted`
- `allow_reason`
- `block_reason`
- `diagnostics`
- `route_enabled`
- `route_frozen_reason`

#### Receipt / reconcile / policy state
Examples:
- `receipt_mode`
- `receipt_accepted`
- `alignment_ok`
- `policy_action`
- `policy_reason`

#### Attribution / account metrics / strategy stats
Examples:
- `account_metrics`
- `attribution_fee_source`
- `attribution_realized_pnl_source`
- `attribution_equity_source`
- `strategy_stats_eligible`
- `strategy_stats_reason`

## Snapshot subtree contracts

### `feature_snapshot`
Purpose:
- curated market/regime input features for background/primary/override windows

Current subtrees:
- `background_4h`
- `primary_15m`
- `override_1m`

Use cases:
- regime analytics
- route/regime dashboard slicing
- later explanation/debug overlays

### `theoretical_snapshot`
Purpose:
- preserve the intended decision context and first-pass execution-deviation math

Contains richer detail than the summary mirror, including:
- action/side/size/reason
- score/subscores/signals/blockers
- decision confidence
- expected notional proxy
- theoretical gross pnl proxy
- fee/funding/realized pnl proxy inputs
- execution drag proxy

Rule:
- if future consumers need more than headline theoretical metrics, read this subtree directly

### `verification_snapshot`
Purpose:
- preserve execution verification attempts and local verification hints

Examples:
- verification attempt list
- trade-confirmed attempt counts
- local position reason/status

### `attribution_snapshot`
Purpose:
- preserve attribution metadata and execution/accounting provenance hints

Examples:
- account / execution / order ids
- trade_count
- fee/realized/equity source hints
- ledger leg-id references

### `ledger_snapshot`
Purpose:
- preserve a compact ledger-oriented view without forcing future consumers to reconstruct everything from raw local-position internals

Current compact shape includes:
- leg counts
- open/closed/pending-exit leg ids

## Strategy-upgrade contract

### `latest-strategy-upgrade-request.json`
Purpose:
- durable request record when active strategy version changes are detected

### `latest-strategy-upgrade-result.json`
Purpose:
- result of processing the upgrade request out-of-band

### `latest-strategy-handover-marker.json`
Purpose:
- explicit handover observation/decision marker for upgrade-time position handling

Related durable state:
- `logs/runtime/strategy-upgrade-state.json`

Purpose:
- remember last-seen strategy version across daemon restarts so upgrade detection remains durable

## Current compatibility rules

### Supported / canonical now
- top-level `result` subtree
- `result.summary`
- snapshot subtrees under `result`
- upgrade artifact family under `logs/runtime/`

### No longer canonical
- top-level mirrored execution summary fields in `latest-execution-cycle.json`
- old `summary.primary_summary` compatibility structure
- old repo-path assumptions under `projects/crypto-trading`
- stale compare/router-composite era structures

## Guidance for future dashboard consumers

Dashboard/report consumers should:
- treat `result.summary` as the main summary contract
- read snapshot subtrees when richer detail is needed
- prefer append-only history files for charts/aggregations
- prefer `latest-execution-cycle.json` only for latest-state views
- treat upgrade artifacts as a separate event family rather than trying to infer upgrades only from execution history

Dashboard/report consumers should **not**:
- depend on removed mirror layers
- depend on broken migration leftovers
- assume fields were removed just because they are not yet shown in reports
- overfit to temporary docs wording instead of the explicit artifact contract here

## Field stability guidance

### Relatively stable now
- file locations under `logs/runtime/`
- top-level shape of `latest-execution-cycle.json`
- use of `result.summary` as the canonical summary layer
- snapshot subtree names
- upgrade artifact family names

### Still evolving
- exact contents of `result.summary`
- exact breadth of preserved statistical fields
- which statistics are later promoted into first-class dashboard/report panels

Current rule for evolving fields:
- prefer preserving potentially valuable structured data
- remove only clearly broken, dead, or purely redundant layers
