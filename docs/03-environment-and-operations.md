# Environment and Operations

## Runtime role

`trading-execution` is the live execution repository.
It consumes the currently promoted trading instructions / active runtime configuration produced by the historical side.

It does **not** define strategy families in-place as the primary control surface.
The live side should focus on:
- reading the active promoted runtime inputs
- executing them continuously
- recording execution artifacts
- exposing execution health and deviation diagnostics

## Environment

Expected in `.env`:
- `OKX_API_KEY`
- `OKX_API_SECRET`
- `OKX_API_PASSPHRASE`
- `OKX_DEMO=true`

Important runtime controls should now be interpreted narrowly around live execution, for example:
- `DRY_RUN=true|false`
- live account / exchange credentials
- runtime artifact paths
- execution-safety toggles
- active strategy / instruction pointer locations

Old strategy-family-specific env examples from the hybrid repo should be treated as transitional only, not as the target control model for this repo.

## Main run paths

### One bounded cycle
```bash
./.venv/bin/python -m src.runners.trade_daemon --max-cycles 1
```

### Normal daemon startup
```bash
./run_daemon.sh
```

### systemd-managed runtime
```bash
systemctl status trading-execution.service --no-pager -n 40
systemctl restart trading-execution.service
```

## Current operating model

- one live account is the current intended operating model
- trade daemon stays up continuously
- active strategy / instruction changes should be detected without daemon restart
- upgrade validation should run out-of-band

## Safety

- designed for OKX demo trading first
- no real-money path should be implied by current docs
- current execution path is still under active hardening
- dry-run vs live-trade state isolation still needs tightening
- when investigating execution anomalies, prefer stopping the daemon first, then repairing exchange/local state, then restarting cleanly

## Bootstrap note

At the current migration stage, this repo should be bootstrapped with a **repo-local virtual environment** rather than system-wide package installation.

Recommended pattern:
- `python3 -m venv .venv`
- `.venv/bin/pip install -r requirements.txt`
- run entrypoints via `.venv/bin/python ...`

This keeps the live-runtime repo reversible and avoids mutating the host Python environment during migration.

## Main code / script touchpoints

- `src/runtime/trade_daemon.py`
- `src/upgrade/strategy_pointer.py`
- `src/execution/pipeline.py`
- `src/upgrade/process_strategy_upgrade_request.py`
- `src/runtime/workflows.py`
- `src/state/`
- `src/reconcile/`
