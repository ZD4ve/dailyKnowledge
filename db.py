import sqlite3
from datetime import datetime

DB_PATH = "articles.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the articles table if it doesn't exist."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                text TEXT,
                authors TEXT,
                publish_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_article(url: str, title: str, text: str,
                 authors: list[str] | None = None,
                 publish_date: datetime | None = None) -> None:
    """Save a single article to the database (skip if URL already exists)."""
    authors_str = ", ".join(authors) if authors else None
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO articles (url, title, text, authors, publish_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (url, title, text, authors_str, publish_date),
        )


def get_articles_by_url(search: str) -> list[dict]:
    """Retrieve all articles whose URL contains the given string."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE url LIKE ? ORDER BY created_at DESC",
            (f"%{search}%",),
        ).fetchall()
    return [dict(row) for row in rows]


def get_processed_urls(search: str) -> set[str]:
    """Return the set of already-saved article URLs that contain the given string."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT url FROM articles WHERE url LIKE ?",
            (f"%{search}%",),
        ).fetchall()
    return {row["url"] for row in rows}


def get_all_articles() -> list[dict]:
    """Return all articles ordered by creation date descending."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_articles_after(date: datetime) -> list[dict]:
    """Return all articles created after the given datetime."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE created_at >= ? ORDER BY created_at DESC",
            (date,),
        ).fetchall()
    return [dict(row) for row in rows]


# Ensure the table exists on first import
init_db()
