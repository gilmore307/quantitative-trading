from __future__ import annotations

from dataclasses import dataclass, field

from src.regimes.models import Regime, RegimeDecision


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
    return RouteDecision(
        regime=regime,
        account='active_live',
        active_route='active_live',
        trade_enabled=True,
        block_reason=None,
        allow_reason='route_to_active_live',
    )


def summarize_decision(decision: RegimeDecision, route: RouteDecision) -> DecisionSummary:
    diagnostics: list[str] = []
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

    trade_enabled = route.trade_enabled
    block_reason = route.block_reason
    allow_reason = route.allow_reason

    if decision.confidence < 0.35:
        trade_enabled = False
        block_reason = 'confidence_too_low'
        allow_reason = None
        diagnostics.append('confidence_gate_blocked')

    route.account = 'active_live'
    route.active_route = 'active_live'

    return DecisionSummary(
        regime=decision.primary.value,
        confidence=decision.confidence,
        tradable=route.trade_enabled,
        account=route.account,
        active_route=route.active_route,
        trade_enabled=trade_enabled,
        allow_reason=allow_reason,
        block_reason=block_reason,
        reasons=list(decision.reasons),
        secondary=[x.value for x in decision.secondary],
        diagnostics=diagnostics,
    )
