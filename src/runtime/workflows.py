from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
import json

from src.config.settings import Settings
from src.exchange.okx_client import OkxClient
from src.review.framework import build_weekly_window
from src.review.export import export_report_artifacts
from src.runtime.mode import RuntimeMode
from src.runtime.store import RuntimeStore
from src.runtime.workflow import next_mode_after


OUT_DIR = Path('/root/.openclaw/workspace/projects/quantitative-trading/logs/runtime')
OUT_DIR.mkdir(parents=True, exist_ok=True)
WORKFLOW_LOG = OUT_DIR / 'workflow-events.jsonl'
TEST_REPORT_JSON = OUT_DIR / 'latest-test-summary.json'
TEST_REPORT_MD = OUT_DIR / 'latest-test-summary.md'


@dataclass(slots=True)
class WorkflowStepResult:
    name: str
    ok: bool
    detail: str | None = None


@dataclass(slots=True)
class WorkflowRunResult:
    workflow: str
    started_mode: str
    ended_mode: str
    destructive: bool
    steps: list[WorkflowStepResult]
    observed_at: datetime


class WorkflowHooks:
    def run_review(self) -> WorkflowStepResult:
        return WorkflowStepResult(name='run_review', ok=True, detail='stub')

    def run_test_workflow(self) -> WorkflowStepResult:
        return WorkflowStepResult(name='run_test_workflow', ok=True, detail='stub')


class OkxWorkflowHooks(WorkflowHooks):
    def __init__(self, settings: Settings):
        self.settings = settings

    def run_review(self) -> WorkflowStepResult:
        try:
            now = datetime.now(UTC)
            window = build_weekly_window(now)
            exported = export_report_artifacts(
                window,
                history_path=str(OUT_DIR / 'execution-cycles.jsonl'),
                out_dir=None,
                generated_at=now,
            )
            return WorkflowStepResult(
                name='run_review',
                ok=True,
                detail=f"json={exported.get('json_path')} markdown={exported.get('markdown_path')}",
            )
        except Exception as exc:
            return WorkflowStepResult(name='run_review', ok=False, detail=str(exc))

    def run_test_workflow(self) -> WorkflowStepResult:
        try:
            self.settings.ensure_demo_only()
            symbol = self.settings.test_symbols[0]
            account_alias = self.settings.test_account_alias
            account = self.settings.strategy_accounts[account_alias]
            client = OkxClient(self.settings, account)
            total_actions: list[str] = []
            cycle_rows: list[dict[str, object]] = []
            entry_count = 0
            add_count = 0
            exit_count = 0
            for cycle in range(self.settings.test_cycles):
                side = 'long'
                if self.settings.test_reverse_signal and cycle % 2 == 1:
                    side = 'short'
                cycle_row: dict[str, object] = {'cycle': cycle + 1, 'side': side, 'entry': None, 'adds': [], 'exit': None}
                entry = client.create_entry_order(symbol, side, float(self.settings.test_entry_usdt))
                entry_count += 1
                cycle_row['entry'] = {'order_id': entry.get('order_id'), 'verified_entry': entry.get('verified_entry'), 'live_contracts': entry.get('live_contracts')}
                total_actions.append(f'cycle={cycle + 1}:entry:{side}:{entry.get("order_id") or "submitted"}')
                current_open_amount = float(entry.get('live_contracts') or entry.get('amount') or 0.0)
                for add_idx in range(self.settings.test_add_count):
                    add = client.create_entry_order(symbol, side, float(self.settings.test_add_usdt), current_open_amount=current_open_amount)
                    add_count += 1
                    current_open_amount = float(add.get('live_contracts') or (current_open_amount + float(add.get('amount') or 0.0)))
                    adds = list(cycle_row.get('adds') or [])
                    adds.append({'order_id': add.get('order_id'), 'verified_entry': add.get('verified_entry'), 'live_contracts': add.get('live_contracts')})
                    cycle_row['adds'] = adds
                    total_actions.append(f'cycle={cycle + 1}:add={add_idx + 1}:{side}:{add.get("order_id") or "submitted"}')
                live = client.current_live_position(symbol)
                if live and float(live.get('contracts') or 0.0) > 0.0 and live.get('side'):
                    exit_result = client.create_exit_order(symbol, str(live.get('side')), float(live.get('contracts') or 0.0))
                    exit_count += 1
                    cycle_row['exit'] = {'order_id': exit_result.get('order_id'), 'verified_flat': exit_result.get('verified_flat'), 'remaining_contracts': exit_result.get('remaining_contracts')}
                    total_actions.append(f'cycle={cycle + 1}:exit:{exit_result.get("order_id") or "submitted"}')
                else:
                    cycle_row['exit'] = {'skipped': True, 'reason': 'no_live_position'}
                    total_actions.append(f'cycle={cycle + 1}:exit_skipped:no_live_position')
                cycle_rows.append(cycle_row)
            summary = {
                'generated_at': datetime.now(UTC).isoformat(),
                'mode': 'test',
                'okx_demo': self.settings.okx_demo,
                'account_alias': account_alias,
                'symbol': symbol,
                'test_cycles': self.settings.test_cycles,
                'test_add_count': self.settings.test_add_count,
                'entry_count': entry_count,
                'add_count': add_count,
                'exit_count': exit_count,
                'cycles': cycle_rows,
            }
            TEST_REPORT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
            markdown_lines = [
                '# Test Mode Summary',
                '',
                f'- Generated at: {summary["generated_at"]}',
                f'- Account: {account_alias}',
                f'- Symbol: {symbol}',
                f'- Cycles: {self.settings.test_cycles}',
                f'- Entries: {entry_count}',
                f'- Adds: {add_count}',
                f'- Exits: {exit_count}',
                '',
                '## Cycle Details',
            ]
            for row in cycle_rows:
                markdown_lines.append(f"- cycle {row['cycle']} side={row['side']} entry={((row.get('entry') or {}).get('order_id') if isinstance(row.get('entry'), dict) else None)} exit={((row.get('exit') or {}).get('order_id') if isinstance(row.get('exit'), dict) else ('skipped' if isinstance(row.get('exit'), dict) and row.get('exit', {}).get('skipped') else None))}")
            TEST_REPORT_MD.write_text('\n'.join(markdown_lines).strip() + '\n', encoding='utf-8')
            return WorkflowStepResult(name='run_test_workflow', ok=True, detail=f"summary_json={TEST_REPORT_JSON} summary_md={TEST_REPORT_MD} | " + ('; '.join(total_actions) if total_actions else 'no_test_actions'))
        except Exception as exc:
            return WorkflowStepResult(name='run_test_workflow', ok=False, detail=str(exc))


class RuntimeWorkflowRunner:
    def __init__(self, runtime_store: RuntimeStore | None = None, hooks: WorkflowHooks | None = None):
        self.runtime_store = runtime_store or RuntimeStore()
        self.hooks = hooks or WorkflowHooks()

    def _log(self, result: WorkflowRunResult) -> None:
        with WORKFLOW_LOG.open('a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(result), default=str, ensure_ascii=False) + '\n')

    def run(self, mode: RuntimeMode) -> WorkflowRunResult:
        if mode not in {RuntimeMode.TEST}:
            raise ValueError(f'workflow mode not supported: {mode}')

        started_mode = self.runtime_store.get().mode
        destructive = False
        self.runtime_store.set_mode(mode, reason='workflow_start')
        steps = [self.hooks.run_test_workflow()]

        transition = next_mode_after(mode)
        ended = mode
        if transition is not None and all(step.ok for step in steps):
            ended = transition.to_mode
            self.runtime_store.set_mode(ended, reason=transition.reason)

        result = WorkflowRunResult(
            workflow=mode.value,
            started_mode=started_mode.value,
            ended_mode=ended.value,
            destructive=destructive,
            steps=steps,
            observed_at=datetime.now(UTC),
        )
        self._log(result)
        return result


def run_review_event(*, hooks: WorkflowHooks | None = None) -> WorkflowRunResult:
    hooks = hooks or WorkflowHooks()
    step = hooks.run_review()
    result = WorkflowRunResult(
        workflow='review_event',
        started_mode=RuntimeMode.TRADE.value,
        ended_mode=RuntimeMode.TRADE.value,
        destructive=False,
        steps=[step],
        observed_at=datetime.now(UTC),
    )
    with WORKFLOW_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(asdict(result), default=str, ensure_ascii=False) + '\n')
    return result


def run_strategy_upgrade_event(*, hooks: WorkflowHooks | None = None, destructive: bool = False) -> dict[str, object]:
    hooks = hooks or WorkflowHooks()
    review_result = run_review_event(hooks=hooks)
    payload = {
        'event': 'strategy_upgrade_event',
        'destructive': destructive,
        'review_result': asdict(review_result),
        'started_mode': RuntimeMode.TRADE.value,
        'ended_mode': RuntimeMode.TRADE.value,
        'observed_at': datetime.now(UTC).isoformat(),
    }
    with WORKFLOW_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(payload, default=str, ensure_ascii=False) + '\n')
    return payload
