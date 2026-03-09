"""Database CRUD operations for Zero-Harm AI."""

from database.connection import get_snowflake_connection
from datetime import datetime
now = datetime.now()
current_dt = now.date()

# --------------- Violation Operations ---------------

def log_violation(
    violation_type: str,
    location: str = "Workshop",
):
    """Log a PPE violation to the database. Snowflake auto-generates the UUID and Timestamp."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO ZERO_HARM_AI.SAFETY.VIOLATIONS
               (VIOLATION_TYPE, LOCATION, TIMESTAMP)
               VALUES (%s, %s, %s)""",
            (violation_type, location, current_dt),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_violations_today() -> list[dict]:
    """Return all violations recorded today."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT ID, VIOLATION_TYPE, TIMESTAMP, LOCATION
               FROM ZERO_HARM_AI.SAFETY.VIOLATIONS
               WHERE DATE(TIMESTAMP) = CURRENT_DATE()
               ORDER BY TIMESTAMP DESC"""
        )
        rows = cursor.fetchall()
        return [
            {
                "violation_id": r[0],
                "violation_type": r[1],
                "timestamp": r[2],
                "location": r[3],
            }
            for r in rows
        ]
    finally:
        cursor.close()
        conn.close()


def get_violation_summary() -> dict:
    """Return aggregated violation stats for today."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    try:
        # Total today
        cursor.execute(
            """SELECT COUNT(*) 
               FROM ZERO_HARM_AI.SAFETY.VIOLATIONS 
               WHERE DATE(TIMESTAMP) = CURRENT_DATE()"""
        )
        total_today = cursor.fetchone()[0]

        # By type
        cursor.execute(
            """SELECT VIOLATION_TYPE, COUNT(*) as cnt
               FROM ZERO_HARM_AI.SAFETY.VIOLATIONS
               WHERE DATE(TIMESTAMP) = CURRENT_DATE()
               GROUP BY VIOLATION_TYPE ORDER BY cnt DESC"""
        )
        by_type = {r[0]: r[1] for r in cursor.fetchall()}

        return {
            "total_today": total_today,
            "by_type": by_type,
        }
    finally:
        cursor.close()
        conn.close()