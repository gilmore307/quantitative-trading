from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategyAccount:
    alias: str
    label: str


ACTIVE_LIVE_ACCOUNT = StrategyAccount(alias="active_live", label="Active Live")

V2_ACCOUNTS: tuple[StrategyAccount, ...] = (
    ACTIVE_LIVE_ACCOUNT,
)
