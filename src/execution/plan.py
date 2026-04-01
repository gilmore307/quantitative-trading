from __future__ import annotations

from dataclasses import dataclass, field

from src.runtime.regime_runner import RegimeRunnerOutput
from src.upgrade.strategy_pointer import ActiveStrategySnapshot


@dataclass(slots=True)
class ExecutionPlan:
    regime: str
    account: str | None
    action: str
    side: str | None = None
    size: float | None = None
    reason: str | None = None
    score: float | None = None
    blockers: list[str] = field(default_factory=list)
    signals: dict = field(default_factory=dict)
    subscores: dict = field(default_factory=dict)


def build_active_strategy_plan(output: RegimeRunnerOutput, active_strategy: ActiveStrategySnapshot | None = None) -> ExecutionPlan:
    label = str((active_strategy.version if active_strategy is not None else '') or ((active_strategy.metadata or {}).get('family') if active_strategy is not None else '') or 'active_live').lower()
    account = output.route_decision.get('account')
    if account is None:
        return ExecutionPlan(regime=str(output.final_decision.get('primary') or 'active_live'), account=None, action='hold', reason='no_active_live_account')
    if label in {'dummy-v1', 'dummy-v2', 'dummy', 'runtime-default', 'default', 'active_live'}:
        return ExecutionPlan(
            regime=str(output.final_decision.get('primary') or label),
            account=account,
            action='watch',
            reason=f'active_strategy_direct:{label}',
            score=float(output.final_decision.get('confidence') or 0.0),
            signals={'active_strategy_label': label, 'final_regime': output.final_decision.get('primary')},
            subscores={'active_strategy_direct': 1.0},
        )
    return ExecutionPlan(
        regime=str(output.final_decision.get('primary') or label),
        account=account,
        action='watch',
        reason=f'active_strategy_direct:{label}',
        score=float(output.final_decision.get('confidence') or 0.0),
        signals={'active_strategy_label': label, 'final_regime': output.final_decision.get('primary')},
        subscores={'active_strategy_direct': 1.0},
    )
