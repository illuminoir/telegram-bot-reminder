import sqlite3
from pathlib import Path

DB_FILE = Path("reminders.db")


# Initialize the database if it doesn't exist
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            timezone_offset INTEGER DEFAULT 0
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            hour INTEGER,
            minute INTEGER,
            run_at TEXT,
            text TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        conn.commit()


def get_conn():
    return sqlite3.connect(DB_FILE)


def set_user_timezone(user_id: int, offset: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (id, timezone_offset)
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET timezone_offset=excluded.timezone_offset
        """, (user_id, offset))
        conn.commit()


def get_user_timezone(user_id: int) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT timezone_offset FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0


def save_daily_reminder(user_id, hour, minute, text):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO reminders (user_id, type, hour, minute, text)
            VALUES (?, 'daily', ?, ?, ?)
        """, (user_id, hour, minute, text)
        )

        reminder_id = cur.lastrowid

        conn.commit()
        return reminder_id


def save_once_reminder(user_id, run_at, text):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO reminders (user_id, type, run_at, text)
            VALUES (?, 'once', ?, ?)
            """,
            (user_id, run_at, text),
        )

        reminder_id = cur.lastrowid

        conn.commit()
        return reminder_id


def delete_once_reminder(reminder_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM reminders WHERE id = ?",
            (reminder_id,),
        )
        conn.commit()
