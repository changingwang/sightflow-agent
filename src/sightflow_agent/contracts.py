"""Provider-neutral message/decision/action contracts. No platform I/O here."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class DecisionKind(str, Enum):
    REPLY = "reply"
    SKIP = "skip"
    ESCALATE = "escalate"


class ReceiptStatus(str, Enum):
    CONFIRMED = "confirmed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceIdentity:
    transport: str
    account_id: str
    session_id: str
    peer_id: str

    def __post_init__(self):
        if not all((self.transport, self.account_id, self.session_id, self.peer_id)):
            raise ValueError("source identity fields must be nonempty")


@dataclass(frozen=True)
class InputEvent:
    event_id: str
    source: SourceIdentity
    text: str
    sender_id: str
    observed_at: float
    evidence_ref: Optional[str] = None


@dataclass(frozen=True)
class PerceptionResult:
    event: InputEvent
    confidence: float
    unresolved: tuple[str, ...] = ()

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence outside [0,1]")


@dataclass(frozen=True)
class Decision:
    kind: DecisionKind
    source: SourceIdentity
    reason: str
    reply_text: Optional[str] = None
    authorization_ref: Optional[str] = None


@dataclass(frozen=True)
class Action:
    action_id: str
    source: SourceIdentity
    kind: str
    payload: Mapping[str, Any]
    authorization_ref: str
    idempotency_key: str


@dataclass(frozen=True)
class Receipt:
    action_id: str
    local_status: ReceiptStatus
    application_status: ReceiptStatus
    business_status: ReceiptStatus = ReceiptStatus.UNKNOWN
    evidence_ref: Optional[str] = None
    error_category: Optional[str] = None

    @property
    def application_confirmed(self) -> bool:
        return self.application_status == ReceiptStatus.CONFIRMED
