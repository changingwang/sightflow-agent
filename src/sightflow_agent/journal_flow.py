"""Journal-backed bounded executor. Start by calling journal.recover()."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .contracts import Action, Decision, DecisionKind, InputEvent, Receipt, ReceiptStatus
from .flow import ActionExecutor, DecisionPolicy, PerceptionAdapter
from .journal import SQLiteActionJournal, JournalStatus


@dataclass(frozen=True)
class JournalFlowResult:
    decision: Decision
    journal_status: JournalStatus | None = None
    receipt: Receipt | None = None
    blocked_reason: str | None = None


def process_once_journal(
    event: InputEvent,
    perceiver: PerceptionAdapter,
    policy: DecisionPolicy,
    executor: ActionExecutor,
    journal: SQLiteActionJournal,
    *,
    authorized: Callable[[Decision], bool],
    minimum_confidence: float = 0.95,
) -> JournalFlowResult:
    """All external sends must flow through this gate.

    A durable reservation is made before calling executor.execute().
    Any ambiguous outcome permanently holds the key for manual reconciliation.
    """
    perception = perceiver.perceive(event)
    decision = policy.decide(perception)
    if decision.source != event.source:
        return JournalFlowResult(decision, blocked_reason="source_identity_mismatch")
    if decision.kind != DecisionKind.REPLY:
        return JournalFlowResult(decision, blocked_reason=decision.kind.value)
    if perception.unresolved or perception.confidence < minimum_confidence:
        return JournalFlowResult(decision, blocked_reason="perception_unresolved")
    if not decision.reply_text or not decision.authorization_ref:
        return JournalFlowResult(decision, blocked_reason="incomplete_action")
    if not authorized(decision):
        return JournalFlowResult(decision, blocked_reason="unauthorized")

    key = ":".join((event.source.transport, event.source.account_id,
                    event.source.session_id, event.source.peer_id, event.event_id))
    if not journal.reserve(key, key):
        existing = journal.get(key)
        return JournalFlowResult(decision, existing.status if existing else None,
                                 blocked_reason="duplicate_or_pending")
    action = Action(
        action_id=key, source=event.source, kind="send_text",
        payload={"text": decision.reply_text},
        authorization_ref=decision.authorization_ref,
        idempotency_key=key,
    )
    if not journal.mark_in_flight(key):
        return JournalFlowResult(decision, JournalStatus.PENDING,
                                 blocked_reason="in_flight_transition_failed")

    try:
        receipt = executor.execute(action)
        if receipt.action_id != action.action_id:
            receipt = Receipt(action.action_id, ReceiptStatus.UNKNOWN,
                              ReceiptStatus.UNKNOWN, error_category="receipt_identity_mismatch")
    except Exception:
        # Do not retry. The side effect may have happened before the exception.
        receipt = Receipt(action.action_id, ReceiptStatus.UNKNOWN,
                          ReceiptStatus.UNKNOWN, error_category="executor_ambiguous")
    status = journal.complete(key, receipt)
    return JournalFlowResult(
        decision, status, receipt,
        None if status == JournalStatus.CONFIRMED else "application_unconfirmed",
    )
