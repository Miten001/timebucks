"""SQLite database for users, scores, and referrals."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from config import DB_PATH


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id        INTEGER PRIMARY KEY,
                username       TEXT,
                first_name     TEXT,
                coins          INTEGER DEFAULT 0,
                games_played   INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                referred_by    INTEGER,
                last_daily     TEXT,
                created_at     TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS redemptions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                coins      INTEGER NOT NULL,
                upi_id     TEXT,
                status     TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_users_coins ON users(coins DESC);
            """
        )


def add_or_get_user(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    referred_by: Optional[int] = None,
) -> dict:
    """Insert user if new, return user row as dict."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

        if row is None:
            db.execute(
                """INSERT INTO users (user_id, username, first_name, referred_by)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, first_name, referred_by),
            )
            row = db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        else:
            # Keep username/first_name fresh
            db.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (username, first_name, user_id),
            )
        return dict(row)


def get_user(user_id: int) -> Optional[dict]:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def add_coins(user_id: int, coins: int) -> int:
    with get_db() as db:
        db.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id = ?",
            (coins, user_id),
        )
        row = db.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["coins"] if row else 0


def deduct_coins(user_id: int, coins: int) -> bool:
    with get_db() as db:
        row = db.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row or row["coins"] < coins:
            return False
        db.execute(
            "UPDATE users SET coins = coins - ? WHERE user_id = ?",
            (coins, user_id),
        )
        return True


def increment_stats(user_id: int, correct: int, played: int = 1) -> None:
    with get_db() as db:
        db.execute(
            """UPDATE users
                  SET games_played = games_played + ?,
                      correct_answers = correct_answers + ?
                WHERE user_id = ?""",
            (played, correct, user_id),
        )


def get_leaderboard(limit: int = 10) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            """SELECT user_id, username, first_name, coins, correct_answers
                 FROM users
                ORDER BY coins DESC
                LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def claim_daily_bonus(user_id: int, bonus: int) -> tuple[bool, int]:
    """Returns (claimed, new_balance). claimed=False if already claimed today."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with get_db() as db:
        row = db.execute(
            "SELECT last_daily, coins FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return False, 0
        if row["last_daily"] == today:
            return False, row["coins"]
        db.execute(
            "UPDATE users SET coins = coins + ?, last_daily = ? WHERE user_id = ?",
            (bonus, today, user_id),
        )
        return True, row["coins"] + bonus


def total_users() -> int:
    with get_db() as db:
        return db.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]


def create_redemption(user_id: int, coins: int, upi_id: str) -> int:
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO redemptions (user_id, coins, upi_id) VALUES (?, ?, ?)",
            (user_id, coins, upi_id),
        )
        return cursor.lastrowid


def get_referral_count(user_id: int) -> int:
    with get_db() as db:
        return db.execute(
            "SELECT COUNT(*) AS c FROM users WHERE referred_by = ?", (user_id,)
        ).fetchone()["c"]
