"""SQLite claim-before-send journal. Ambiguous outcomes are never retried automatically."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .contracts import Receipt, ReceiptStatus


class JournalStatus(str, Enum):
    PENDING = "PENDING"
    IN_FLIGHT = "IN_FLIGHT"
    UNKNOWN = "UNKNOWN"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class JournalEntry:
    action_key: str
    status: JournalStatus
    action_id: str
    error_category: str | None


class SQLiteActionJournal:
    """Durable, single-key exclusive journal.

    Key must be globally scoped by authenticated account, session and event id.
    Call recover() at startup before processing any input.
    """

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._db = sqlite3.connect(self.path, isolation_level=None, timeout=30)
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA busy_timeout=30000")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                action_key TEXT PRIMARY KEY,
                action_id TEXT NOT NULL,
                status TEXT NOT NULL,
                local_status TEXT,
                application_status TEXT,
                business_status TEXT,
                evidence_ref TEXT,
                error_category TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

    def close(self):
        self._db.close()

    def _begin(self):
        self._db.execute("BEGIN IMMEDIATE")

    def reserve(self, action_key: str, action_id: str) -> bool:
        """Atomically claim the key before any external side effect."""
        if not action_key or not action_id:
            raise ValueError("action identity required")
        now = time.time()
        self._begin()
        try:
            row = self._db.execute(
                "SELECT 1 FROM actions WHERE action_key=?", (action_key,)
            ).fetchone()
            if row:
                self._db.execute("COMMIT")
                return False
            self._db.execute(
                "INSERT INTO actions (action_key,action_id,status,created_at,updated_at)"
                " VALUES (?,?,?,?,?)",
                (action_key, action_id, JournalStatus.PENDING.value, now, now),
            )
            self._db.execute("COMMIT")
            return True
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    def mark_in_flight(self, action_key: str) -> bool:
        """Durably record that external side effects may begin."""
        self._begin()
        try:
            cur = self._db.execute(
                "UPDATE actions SET status=?,updated_at=? "
                "WHERE action_key=? AND status=?",
                (JournalStatus.IN_FLIGHT.value, time.time(), action_key,
                 JournalStatus.PENDING.value),
            )
            self._db.execute("COMMIT")
            return cur.rowcount == 1
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    def complete(self, action_key: str, receipt: Receipt) -> JournalStatus:
        """Persist the receipt. UNKNOWN is sticky and blocks blind resend."""
        status = (
            JournalStatus.CONFIRMED
            if receipt.application_status == ReceiptStatus.CONFIRMED
            else JournalStatus.FAILED
            if receipt.application_status == ReceiptStatus.FAILED
            else JournalStatus.UNKNOWN
        )
        self._begin()
        try:
            row = self._db.execute(
                "SELECT action_id,status FROM actions WHERE action_key=?", (action_key,)
            ).fetchone()
            if not row or row[0] != receipt.action_id or row[1] != JournalStatus.IN_FLIGHT.value:
                raise ValueError("receipt must match an in-flight action")
            self._db.execute(
                "UPDATE actions SET status=?,local_status=?,application_status=?,"
                "business_status=?,evidence_ref=?,error_category=?,updated_at=? "
                "WHERE action_key=?",
                (status.value, receipt.local_status.value,
                 receipt.application_status.value, receipt.business_status.value,
                 receipt.evidence_ref, receipt.error_category, time.time(), action_key),
            )
            self._db.execute("COMMIT")
            return status
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    def recover(self) -> int:
        """Fail-closed: pending and in-flight actions become UNKNOWN after restart."""
        self._begin()
        try:
            cur = self._db.execute(
                "UPDATE actions SET status=?,error_category=?,updated_at=? "
                "WHERE status IN (?,?)",
                (JournalStatus.UNKNOWN.value, "restart_ambiguous", time.time(),
                 JournalStatus.PENDING.value, JournalStatus.IN_FLIGHT.value),
            )
            self._db.execute("COMMIT")
            return cur.rowcount
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    def get(self, action_key: str) -> JournalEntry | None:
        row = self._db.execute(
            "SELECT action_key,status,action_id,error_category "
            "FROM actions WHERE action_key=?", (action_key,)
        ).fetchone()
        return JournalEntry(row[0], JournalStatus(row[1]), row[2], row[3]) if row else None
