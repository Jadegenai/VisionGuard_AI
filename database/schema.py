"""Snowflake schema setup for Zero-Harm AI."""

from database.connection import get_snowflake_connection

SCHEMA_SQL = [
    """
    CREATE DATABASE IF NOT EXISTS ZERO_HARM_AI;
    """,
    """
    USE DATABASE ZERO_HARM_AI;
    """,
    """
    CREATE SCHEMA IF NOT EXISTS SAFETY;
    """,
    """
    USE SCHEMA SAFETY;
    """,
    """
    CREATE TABLE IF NOT EXISTS ppe_violations (
        violation_id INTEGER AUTOINCREMENT PRIMARY KEY,
        violation_type VARCHAR(50) NOT NULL,
        timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
        location VARCHAR(100) DEFAULT 'Workshop',
        image_path VARCHAR(500),
        created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    );
    """,
]


def initialize_database():
    """Create the database tables if they don't exist."""
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    try:
        for sql in SCHEMA_SQL:
            cursor.execute(sql.strip())
        print("Database schema initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    initialize_database()
