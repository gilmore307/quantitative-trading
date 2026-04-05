# trading-execution

Realtime trading, execution, runtime operations, and live monitoring codebase.

This repository should retain:
- live runtime workflows
- execution submission / confirm / reconcile
- live state persistence
- strategy upgrade / promotion operational handling
- realtime alerts / notifications
- operational review of live trading behavior
- machine-readable runtime/review artifacts consumed downstream by `trading-report`

Historical data ingestion, research, model building, and backtests are being retained in:
- `trading-model`

Reporting boundary:
- `trading-execution` owns runtime/review producer artifacts
- `trading-report` owns the unified downstream final report assembly built on top of those artifacts

Start here:
- `docs/README.md`
- `src/README.md`

Repository structure note:
- `src/` is the authoritative live/runtime code
- the older `flows/` migration workspace has been retired to avoid duplicate logic and maintenance confusion
- regime labels inside the codebase (`trend`, `range`, `compression`, `crowded`, `shock`) describe market/execution decision categories, not separate live accounts
