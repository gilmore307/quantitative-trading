from __future__ import annotations

import argparse
import fcntl
import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config.settings import Settings
from src.execution.adapters import DryRunExecutionAdapter, OkxExecutionAdapter
from src.execution.pipeline import ExecutionPipeline
from src.ops.discord_notifier import DiscordNotifier
from src.execution_cycle import persist_active_strategy_execution_artifact
from src.state.log_paths import RUNTIME_DIR, dated_jsonl_path
from src.runtime.mode import RuntimeMode
from src.runtime.store import RuntimeStore
from src.upgrade.strategy_pointer import load_active_strategy_snapshot
from src.runtime.workflows import OkxWorkflowHooks, WorkflowHooks, WorkflowRunResult
from src.runtime.dummy_cycle import run_dummy_cycle

OUT_DIR = RUNTIME_DIR
DAEMON_LOG = lambda: dated_jsonl_path('trade-daemon')
PID_PATH = OUT_DIR / 'trade-daemon.pid'
LOCK_PATH = OUT_DIR / 'trade-daemon.lock'
UPGRADE_REQUEST_PATH = OUT_DIR / 'latest-strategy-upgrade-request.json'
UPGRADE_STATE_PATH = OUT_DIR / 'strategy-upgrade-state.json'


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return str(value)


def _log_event(event: dict[str, Any]) -> None:
    with DAEMON_LOG().open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event, default=_json_default, ensure_ascii=False) + '\n')


def _store_upgrade_request(event: dict[str, Any]) -> None:
    UPGRADE_REQUEST_PATH.write_text(json.dumps(event, default=_json_default, ensure_ascii=False, indent=2), encoding='utf-8')


def _load_upgrade_state() -> dict[str, Any]:
    if not UPGRADE_STATE_PATH.exists():
        return {}
    try:
        payload = json.loads(UPGRADE_STATE_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _store_upgrade_state(payload: dict[str, Any]) -> None:
    UPGRADE_STATE_PATH.write_text(json.dumps(payload, default=_json_default, ensure_ascii=False, indent=2), encoding='utf-8')


def _maybe_emit_upgrade_request(*, active_strategy, cycle_started_at: datetime, state: dict[str, Any]) -> dict[str, Any]:
    current_version = str(active_strategy.version)
    previous_version = str(state.get('last_seen_strategy_version') or '')
    pending_request_version = str(state.get('pending_request_version') or '')
    last_request_version = str(state.get('last_request_version') or '')

    if not previous_version:
        state['last_seen_strategy_version'] = current_version
        state['last_seen_at'] = cycle_started_at
        return state

    version_changed = current_version != previous_version
    request_needed = version_changed and current_version not in {pending_request_version, last_request_version}

    if request_needed:
        _log_event({
            'event': 'strategy_hot_swap_detected',
            'observed_at': cycle_started_at,
            'previous_version': previous_version,
            'active_strategy_version': current_version,
            'active_strategy_source': active_strategy.source,
            'active_strategy_label': active_strategy.metadata.get('family'),
            'active_strategy_config_path': active_strategy.metadata.get('config_path'),
            'active_strategy_promoted_at': active_strategy.metadata.get('promoted_at'),
            'promotion_note': active_strategy.metadata.get('promotion_note'),
        })
        request_event = {
            'event': 'strategy_upgrade_event_requested',
            'observed_at': cycle_started_at,
            'previous_version': previous_version,
            'active_strategy_version': current_version,
            'active_strategy_source': active_strategy.source,
            'request_reason': 'detected_active_strategy_version_change',
            'execution_policy': 'deferred_out_of_band',
            'position_handover_policy': 'strategy_switch_handling',
        }
        _log_event(request_event)
        _store_upgrade_request(request_event)
        state['pending_request_version'] = current_version
        state['last_request_version'] = current_version
        state['last_request_at'] = cycle_started_at

    state['last_seen_strategy_version'] = current_version
    state['last_seen_at'] = cycle_started_at
    return state


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run continuous trade daemon for crypto-trading demo execution.')
    parser.add_argument('--interval-seconds', type=float, default=60.0, help='Seconds between execution cycles.')
    parser.add_argument('--max-cycles', type=int, default=0, help='Optional max cycles for bounded runs. 0 means run forever.')
    parser.add_argument('--dummy-live-cycle', action='store_true', help='Run deterministic dummy enter/exit cycles based on promoted strategy version metadata.')
    return parser


def acquire_single_instance_lock():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK_PATH.open('a+', encoding='utf-8')
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.seek(0)
        holder = handle.read().strip()
        raise RuntimeError(f'trade_daemon_lock_held:{holder or "unknown"}') from exc
    handle.seek(0)
    handle.truncate()
    handle.write(str(Path('/proc/self').resolve().name))
    handle.flush()
    return handle


def ensure_trade_start_ready(*, settings: Settings, runtime_store: RuntimeStore, hooks: WorkflowHooks | None = None) -> WorkflowRunResult | None:
    if runtime_store.get().mode != RuntimeMode.TRADE:
        return None
    return None


def main() -> None:
    args = build_arg_parser().parse_args()
    daemon_lock = acquire_single_instance_lock()
    settings = Settings.load()
    settings.ensure_demo_only()

    runtime_store = RuntimeStore()
    runtime_store.set_mode(RuntimeMode.TRADE, reason='daemon_start_trade_mode')

    startup_workflow = ensure_trade_start_ready(settings=settings, runtime_store=runtime_store)

    notifier = DiscordNotifier(settings)
    adapter = DryRunExecutionAdapter() if settings.dry_run else OkxExecutionAdapter(settings)
    pipeline = ExecutionPipeline(settings=settings, runtime_store=runtime_store, adapter=adapter)
    upgrade_state = _load_upgrade_state()

    PID_PATH.write_text(str(Path('/proc/self').resolve().name), encoding='utf-8')
    _log_event({
        'event': 'daemon_started',
        'observed_at': datetime.now(UTC),
        'interval_seconds': args.interval_seconds,
        'dry_run': settings.dry_run,
        'dummy_live_cycle': args.dummy_live_cycle,
        'mode': runtime_store.get().mode.value,
        'startup_workflow': None if startup_workflow is None else {
            'workflow': startup_workflow.workflow,
            'started_mode': startup_workflow.started_mode,
            'ended_mode': startup_workflow.ended_mode,
            'steps': [asdict(step) for step in startup_workflow.steps],
        },
    })

    cycles = 0
    while True:
        cycle_started_at = datetime.now(UTC)
        try:
            active_strategy = load_active_strategy_snapshot()
            upgrade_state = _maybe_emit_upgrade_request(active_strategy=active_strategy, cycle_started_at=cycle_started_at, state=upgrade_state)
            _store_upgrade_state(upgrade_state)
            result = run_dummy_cycle(runtime_store=runtime_store, active=active_strategy) if args.dummy_live_cycle else pipeline.run_cycle_active_strategy()
            artifact = persist_active_strategy_execution_artifact(result)
            primary = artifact.get('result', {}) if isinstance(artifact, dict) else {}
            primary_summary = primary.get('summary', {}) if isinstance(primary, dict) else {}
            cycle_event = {
                'event': 'cycle_ok',
                'observed_at': cycle_started_at,
                'runtime_mode': primary_summary.get('runtime_mode'),
                'active_strategy_version': primary_summary.get('active_strategy_version'),
                'active_strategy_label': primary_summary.get('active_strategy_label'),
                'symbol': primary_summary.get('symbol'),
                'regime': primary_summary.get('regime'),
                'plan_action': primary_summary.get('plan_action'),
                'plan_account': primary_summary.get('plan_account'),
                'trade_enabled': primary_summary.get('trade_enabled'),
                'pipeline_entered': primary_summary.get('pipeline_entered'),
                'submission_allowed': primary_summary.get('submission_allowed'),
                'submission_attempted': primary_summary.get('submission_attempted'),
                'block_reason': primary_summary.get('block_reason'),
                'allow_reason': primary_summary.get('allow_reason'),
                'execution_drag_proxy_usdt': primary_summary.get('execution_drag_proxy_usdt'),
            }
            _log_event(cycle_event)

            notifier.notify_trade(primary_summary, primary)
            notifier.notify_warning(primary_summary)
        except Exception as exc:
            error_event = {
                'event': 'cycle_error',
                'observed_at': cycle_started_at,
                'error': repr(exc),
            }
            _log_event(error_event)
            notifier.notify_error(error_event)

        cycles += 1
        if args.max_cycles > 0 and cycles >= args.max_cycles:
            break
        time.sleep(max(1.0, args.interval_seconds))

    _log_event({
        'event': 'daemon_stopped',
        'observed_at': datetime.now(UTC),
        'cycles': cycles,
    })
    daemon_lock.close()


if __name__ == '__main__':
    main()
