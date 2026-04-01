# Research / Runtime Separation (Live Side)

This document keeps only the runtime-side interpretation of research/runtime separation.

## Goal

Keep live runtime execution operationally independent from historical research.

## Runtime path responsibilities

Entry:
- `src/runners/trade_daemon.py`

Responsibilities:
- fetch current market/exchange state
- run execution pipeline
- reconcile local/exchange state
- place demo/live orders when allowed
- persist runtime artifacts
- send operational notifications

## Runtime must not require

- offline research runners
- historical replay inputs
- batch report generation to complete a cycle

## Rule

Artifact compatibility is allowed; operational dependence is not.

Research may consume runtime artifacts.
Runtime should not need research processes to stay alive.
