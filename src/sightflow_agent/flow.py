"""Bounded decision -> action -> receipt loop, with fail-closed behavior."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from .contracts import (
    Action, Decision, DecisionKind, InputEvent, PerceptionResult,
    Receipt, ReceiptStatus,
)


class InputAdapter(Protocol):
    def read(self) -> list[InputEvent]: ...


class PerceptionAdapter(Protocol):
    def perceive(self, event: InputEvent) -> PerceptionResult: ...


class DecisionPolicy(Protocol):
    def decide(self, perception: PerceptionResult) -> Decision: ...


class ActionExecutor(Protocol):
    def execute(self, action: Action) -> Receipt: ...


class ReceiptStore(Protocol):
    def recorded(self, idempotency_key: str) -> bool: ...
    def save(self, idempotency_key: str, receipt: Receipt) -> None: ...


@dataclass(frozen=True)
class FlowResult:
    decision: Decision
    receipt: Receipt | None = None
    blocked_reason: str | None = None


def process_once(
    event: InputEvent,
    perceiver: PerceptionAdapter,
    policy: DecisionPolicy,
    executor: ActionExecutor,
    store: ReceiptStore,
    *,
    minimum_confidence: float = 0.95,
    authorized: Callable[[Decision], bool] = lambda _: False,
) -> FlowResult:
    """Execute at most one authorized reply. Any uncertainty blocks execution.

    The host must provide independent authorization and durable receipt storage.
    A confirmed receipt is application-level evidence, not proof of delivery.
    """
    perception = perceiver.perceive(event)
    decision = policy.decide(perception)
    if decision.source != event.source:
        return FlowResult(decision, blocked_reason="source_identity_mismatch")
    if decision.kind != DecisionKind.REPLY:
        return FlowResult(decision, blocked_reason=decision.kind.value)
    if perception.unresolved or perception.confidence < minimum_confidence:
        return FlowResult(decision, blocked_reason="perception_unresolved")
    if not decision.reply_text or not decision.authorization_ref:
        return FlowResult(decision, blocked_reason="incomplete_action")
    if not authorized(decision):
        return FlowResult(decision, blocked_reason="unauthorized")
    key = ":".join((event.source.account_id, event.source.session_id, event.event_id))
    if store.recorded(key):
        return FlowResult(decision, blocked_reason="already_recorded")
    action = Action(
        action_id=key, source=event.source, kind="send_text",
        payload={"text": decision.reply_text},
        authorization_ref=decision.authorization_ref,
        idempotency_key=key,
    )
    receipt = executor.execute(action)
    store.save(key, receipt)
    if receipt.application_status != ReceiptStatus.CONFIRMED:
        return FlowResult(decision, receipt, blocked_reason="application_unconfirmed")
    return FlowResult(decision, receipt)
