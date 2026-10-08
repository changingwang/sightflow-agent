"""Offline tests: sqlite journal survives restart and blocks ambiguous resends."""
import tempfile
import unittest
from pathlib import Path

from sightflow_agent.contracts import (
    SourceIdentity, InputEvent, PerceptionResult, Decision, DecisionKind,
    Receipt, ReceiptStatus,
)
from sightflow_agent.journal import SQLiteActionJournal, JournalStatus
from sightflow_agent.journal_flow import process_once_journal

SRC = SourceIdentity("fixture", "acct", "session", "peer")
EVENT = InputEvent("evt", SRC, "hello", "peer", 0.0)

class Perceiver:
    def perceive(self, event):
        return PerceptionResult(event, 1.0)

class Policy:
    def decide(self, perception):
        return Decision(DecisionKind.REPLY, SRC, "reply", "hi", "auth")

class Executor:
    def __init__(self, *, crash=False, status=ReceiptStatus.CONFIRMED):
        self.calls = 0
        self.crash = crash
        self.status = status

    def execute(self, action):
        self.calls += 1
        if self.crash:
            raise OSError("after possible send")
        return Receipt(action.action_id, ReceiptStatus.CONFIRMED, self.status)


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "journal.db"
        self.journal = SQLiteActionJournal(self.path)

    def tearDown(self):
        self.journal.close()
        self.temp.cleanup()

    def run_flow(self, executor, authorized=lambda _: True):
        return process_once_journal(EVENT, Perceiver(), Policy(), executor,
                                    self.journal, authorized=authorized)

    def test_confirmed_not_repeated(self):
        ex = Executor()
        self.assertEqual(self.run_flow(ex).journal_status, JournalStatus.CONFIRMED)
        self.assertEqual(self.run_flow(ex).blocked_reason, "duplicate_or_pending")
        self.assertEqual(ex.calls, 1)

    def test_exception_is_unknown_and_not_retried(self):
        ex = Executor(crash=True)
        self.assertEqual(self.run_flow(ex).journal_status, JournalStatus.UNKNOWN)
        self.assertEqual(self.run_flow(ex).blocked_reason, "duplicate_or_pending")
        self.assertEqual(ex.calls, 1)

    def test_restart_after_mark_in_flight(self):
        self.assertTrue(self.journal.reserve("other", "other"))
        self.assertTrue(self.journal.mark_in_flight("other"))
        self.journal.close()
        self.journal = SQLiteActionJournal(self.path)
        self.assertEqual(self.journal.recover(), 1)
        self.assertEqual(self.journal.get("other").status, JournalStatus.UNKNOWN)
        self.assertFalse(self.journal.reserve("other", "other"))

    def test_restart_pending_also_held(self):
        self.assertTrue(self.journal.reserve("other", "other"))
        self.journal.close()
        self.journal = SQLiteActionJournal(self.path)
        self.assertEqual(self.journal.recover(), 1)
        self.assertEqual(self.journal.get("other").status, JournalStatus.UNKNOWN)

    def test_unknown_receipt_is_not_success(self):
        ex = Executor(status=ReceiptStatus.UNKNOWN)
        r = self.run_flow(ex)
        self.assertEqual(r.journal_status, JournalStatus.UNKNOWN)
        self.assertEqual(r.blocked_reason, "application_unconfirmed")

    def test_unauthorized_has_no_reservation(self):
        ex = Executor()
        r = self.run_flow(ex, authorized=lambda _: False)
        self.assertEqual(r.blocked_reason, "unauthorized")
        self.assertEqual(ex.calls, 0)
        self.assertIsNone(self.journal.get("fixture:acct:session:peer:evt"))

    def test_exclusive_reservation_across_connections(self):
        second = SQLiteActionJournal(self.path)
        try:
            self.assertTrue(self.journal.reserve("key", "key"))
            self.assertFalse(second.reserve("key", "key"))
        finally:
            second.close()

    def test_mismatched_receipt_identity_is_unknown(self):
        class WrongExecutor:
            def execute(self, action):
                return Receipt("wrong", ReceiptStatus.CONFIRMED, ReceiptStatus.CONFIRMED)
        self.assertEqual(self.run_flow(WrongExecutor()).journal_status, JournalStatus.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
