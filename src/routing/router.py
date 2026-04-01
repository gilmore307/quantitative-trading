from __future__ import annotations

from dataclasses import dataclass, field

from src.regimes.models import Regime, RegimeDecision


REGIME_ACCOUNT_MAP: dict[Regime, str | None] = {
    Regime.TREND: "active_live",
    Regime.RANGE: "active_live",
    Regime.COMPRESSION: "active_live",
    Regime.CROWDED: "active_live",
    Regime.SHOCK: "active_live",
    Regime.CHAOTIC: None,
}


@dataclass(slots=True)
class RouteDecision:
    regime: Regime
    account: str | None
    active_route: str | None
    trade_enabled: bool
    block_reason: str | None = None
    allow_reason: str | None = None


@dataclass(slots=True)
class DecisionSummary:
    regime: str
    confidence: float
    tradable: bool
    account: str | None
    active_route: str | None
    trade_enabled: bool
    allow_reason: str | None
    block_reason: str | None
    reasons: list[str] = field(default_factory=list)
    secondary: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


def route_regime(regime: Regime) -> RouteDecision:
    account = REGIME_ACCOUNT_MAP[regime]
    trade_enabled = account is not None
    block_reason = None if trade_enabled else 'no_route_for_regime'
    allow_reason = f'route_to_{account}' if trade_enabled else None
    return RouteDecision(
        regime=regime,
        account=account,
        active_route='active_live' if account is not None else None,
        trade_enabled=trade_enabled,
        block_reason=block_reason,
        allow_reason=allow_reason,
    )


def summarize_decision(decision: RegimeDecision, route: RouteDecision) -> DecisionSummary:
    diagnostics: list[str] = []
    if not decision.tradable:
        diagnostics.append('regime_marked_non_tradable')
    if route.account is None:
        diagnostics.append('no_active_live_route')
    if decision.confidence < 0.5:
        diagnostics.append('low_confidence')
    elif decision.confidence < 0.7:
        diagnostics.append('moderate_confidence')
    else:
        diagnostics.append('high_confidence')

    if len(decision.secondary) >= 2:
        diagnostics.append('multi_candidate_regimes')
    elif len(decision.secondary) == 1:
        diagnostics.append('single_runner_up_regime')

    trade_enabled = decision.tradable and route.trade_enabled
    block_reason = route.block_reason
    allow_reason = route.allow_reason

    if not decision.tradable:
        block_reason = 'regime_non_tradable'
        allow_reason = None
    elif route.account is None:
        block_reason = route.block_reason or 'no_active_live_route'
        allow_reason = None
    elif decision.confidence < 0.35:
        trade_enabled = False
        block_reason = 'confidence_too_low'
        allow_reason = None
        diagnostics.append('confidence_gate_blocked')

    return DecisionSummary(
        regime=decision.primary.value,
        confidence=decision.confidence,
        tradable=decision.tradable,
        account=route.account,
        active_route=route.active_route,
        trade_enabled=trade_enabled,
        allow_reason=allow_reason,
        block_reason=block_reason,
        reasons=list(decision.reasons),
        secondary=[x.value for x in decision.secondary],
        diagnostics=diagnostics,
    )
