from __future__ import annotations
import uuid
from typing import Any, Dict, Optional, List
from psycopg import sql
from psycopg.types.json import Json
from .pool import get_conn
from .time_utils import now_th

# Users

def create_or_get_user(student_id: str, name: str, email: Optional[str] = None, preferences: Optional[Dict[str, Any]] = None) -> str:
    """Insert user if not exists by student_id, return user_id."""
    with get_conn() as conn, conn.cursor() as cur:
        # Try to find existing
        cur.execute("SELECT user_id FROM users WHERE student_id=%s", (student_id,))
        row = cur.fetchone()
        if row:
            return row["user_id"]
        user_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO users (user_id, student_id, name, email, preferences, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, student_id, name, email, Json(preferences) if preferences is not None else None, now_th().replace(tzinfo=None)),
        )
        return user_id


def update_user_last_login(user_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("UPDATE users SET last_login=%s WHERE user_id=%s", (now_th().replace(tzinfo=None), user_id))


# Cases

def upsert_case(case_id: str, case_name: str, case_type: str, case_data: Dict[str, Any]):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cases (case_id, case_name, case_type, case_data, import_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (case_id) DO UPDATE SET
              case_name = EXCLUDED.case_name,
              case_type = EXCLUDED.case_type,
              case_data = EXCLUDED.case_data
            """,
            (case_id, case_name, case_type, Json(case_data), now_th().replace(tzinfo=None)),
        )


def list_cases() -> List[Dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT case_id, case_name, case_type FROM cases ORDER BY case_id")
        return cur.fetchall()


def list_cases_detailed() -> List[Dict[str, Any]]:
    """Return list of cases with fields needed by UI, extracted from JSONB."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              case_id,
              case_name,
              case_type,
              (case_data->'case_metadata'->>'case_title') AS case_title,
              (case_data->'case_metadata'->>'medical_specialty') AS medical_specialty,
              NULLIF((case_data->'case_metadata'->>'exam_duration_minutes'), '')::INT AS exam_duration_minutes
            FROM cases
            ORDER BY case_id
            """
        )
        return cur.fetchall()


def next_case_id(prefix: str) -> str:
    """Compute the next case_id for a given prefix (e.g., '01' -> '01_04')."""
    if not prefix or len(prefix) != 2 or not prefix.isdigit():
        raise ValueError("prefix must be a two-digit string like '01' or '02'")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(MAX(CAST(split_part(case_id,'_',2) AS INTEGER)), 0)
            FROM cases
            WHERE split_part(case_id,'_',1) = %s
            """,
            (prefix,),
        )
        row = cur.fetchone()
        max_n = int(list(row.values())[0]) if row else 0
        return f"{prefix}_{max_n + 1:02d}"

def get_case_data(case_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT case_data FROM cases WHERE case_id=%s", (case_id,))
        row = cur.fetchone()
        return row["case_data"] if row else None


# Sessions

def create_session(session_id: str, user_id: str, case_id: str, started_at) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (session_id, user_id, case_id, status, started_at)
            VALUES (%s, %s, %s, 'active', %s)
            """,
            (session_id, user_id, case_id, started_at),
        )


def complete_session(session_id: str, total_tokens: int, ended_at, duration_seconds: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE sessions
            SET status='completed', ended_at=%s, duration_seconds=%s, total_tokens=%s
            WHERE session_id=%s
            """,
            (ended_at, duration_seconds, total_tokens, session_id),
        )


# Chat messages

def add_chat_message(session_id: str, role: str, content: str, timestamp, tokens_used: int = 0, response_time_ms: Optional[int] = None) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chat_messages (content, session_id, role, timestamp, tokens_used, response_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING message_id
            """,
            (content, session_id, role, timestamp, tokens_used, response_time_ms),
        )
        row = cur.fetchone()
        return int(row["message_id"]) if row else 0


# Session reports

def insert_session_report(session_id: str, summary: Dict[str, Any], generated_at, report_id: Optional[str] = None) -> str:
    rid = report_id or str(uuid.uuid4())
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO session_reports (report_id, session_id, generated_at, summary)
            VALUES (%s, %s, %s, %s)
            """,
            (rid, session_id, generated_at, Json(summary)),
        )
    return rid


# Audit log

def add_audit_log(user_id: Optional[str], session_id: Optional[str], action_type: str, performed_at) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_log (user_id, session_id, action_type, performed_at)
            VALUES (%s, %s, %s, %s)
            RETURNING log_id
            """,
            (user_id, session_id, action_type, performed_at),
        )
        row = cur.fetchone()
        return int(row["log_id"]) if row else 0
