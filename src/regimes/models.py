from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Regime(StrEnum):
    TREND = "trend"
    RANGE = "range"
    COMPRESSION = "compression"
    CROWDED = "crowded"
    SHOCK = "shock"
    CHAOTIC = "chaotic"


@dataclass(slots=True)
class RegimeDecision:
    primary: Regime
    confidence: float
    reasons: list[str] = field(default_factory=list)
    secondary: list[Regime] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def tradable(self) -> bool:
        return True
