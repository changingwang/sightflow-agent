"""Pure fixture tests; do not connect to or send messages through WeChat."""
import unittest

from sightflow_agent.contracts import (
    Decision, DecisionKind, InputEvent, PerceptionResult,
    Receipt, ReceiptStatus, SourceIdentity,
)
from sightflow_agent.flow import process_once


SOURCE = SourceIdentity("fixture", "account-a", "session-a", "peer-a")
EVENT = InputEvent("event-a", SOURCE, "hello", "peer-a", 0.0)


class Perceiver:
    def __init__(self, confidence=1.0, unresolved=()):
        self.confidence, self.unresolved = confidence, unresolved

    def perceive(self, event):
        return PerceptionResult(event, self.confidence, self.unresolved)


class Policy:
    def __init__(self, kind=DecisionKind.REPLY, source=SOURCE):
        self.kind, self.source = kind, source

    def decide(self, perceived):
        return Decision(self.kind, self.source, "fixture", "hello back", "owner-consent")


class Executor:
    def __init__(self, status=ReceiptStatus.CONFIRMED):
        self.calls = []
        self.status = status

    def execute(self, action):
        self.calls.append(action)
        return Receipt(action.action_id, ReceiptStatus.CONFIRMED, self.status)


class Store:
    def __init__(self):
        self.data = {}

    def recorded(self, key):
        return key in self.data

    def save(self, key, receipt):
        self.data[key] = receipt


class FlowContractTests(unittest.TestCase):
    def setUp(self):
        self.executor = Executor()
        self.store = Store()

    def run_flow(self, perceiver=None, policy=None, authorized=lambda _: True):
        return process_once(EVENT, perceiver or Perceiver(), policy or Policy(),
                            self.executor, self.store, authorized=authorized)

    def test_confirmed_once(self):
        first = self.run_flow()
        self.assertIsNone(first.blocked_reason)
        self.assertEqual(len(self.executor.calls), 1)
        second = self.run_flow()
        self.assertEqual(second.blocked_reason, "already_recorded")
        self.assertEqual(len(self.executor.calls), 1)

    def test_authorization_denied(self):
        result = self.run_flow(authorized=lambda _: False)
        self.assertEqual(result.blocked_reason, "unauthorized")
        self.assertEqual(len(self.executor.calls), 0)

    def test_unresolved_perception(self):
        result = self.run_flow(Perceiver(0.5, ("target",)))
        self.assertEqual(result.blocked_reason, "perception_unresolved")

    def test_wrong_source(self):
        foreign = SourceIdentity("fixture", "other", "session-a", "peer-a")
        result = self.run_flow(policy=Policy(source=foreign))
        self.assertEqual(result.blocked_reason, "source_identity_mismatch")

    def test_skip(self):
        result = self.run_flow(policy=Policy(kind=DecisionKind.SKIP))
        self.assertEqual(result.blocked_reason, "skip")

    def test_unconfirmed_is_saved_for_manual_review(self):
        self.executor.status = ReceiptStatus.UNKNOWN
        result = self.run_flow()
        self.assertEqual(result.blocked_reason, "application_unconfirmed")
        self.assertEqual(len(self.store.data), 1)
        self.assertEqual(self.run_flow().blocked_reason, "already_recorded")


if __name__ == "__main__":
    unittest.main()
