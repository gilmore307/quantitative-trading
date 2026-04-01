# 10 Research / Runtime Separation (Live Side)

This flow step collects the live-only runtime pieces that must stay operationally independent from historical research.

## Responsibility

- keep the live runtime autonomous
- keep notifier / watcher / loop helpers on the runtime side
- make it clear which runtime helpers belong to the live system rather than the historical modeling system

## Current contents

### engines
- `engines/realtime_engine.py`
- `engines/minute_engine.py`

### monitors
- `monitors/shock_monitor.py`
- `monitors/trade_alert_watcher.py`

### notifications
- `notifications/discord_notifier.py`

### runtime-helpers
- `runtime-helpers/business_time.py`
- `runtime-helpers/bucket_state.py`

## Expected future home

These files will likely land across final `src/runners/`, `src/runtime/`, and notification/ops helper areas inside `quantitative-trading`.
