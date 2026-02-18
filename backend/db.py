import sqlite3
from datetime import datetime
from helper import dataArticle

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
                site_name TEXT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                text TEXT,
                authors TEXT,
                publish_date TIMESTAMP,
                score INTEGER DEFAULT -1,
                summary TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

def save_article(site_name: str, url: str, title: str, text: str,
                 authors: list[str] | None = None,
                 publish_date: datetime | None = None) -> None:
    """Save a single article to the database (skip if URL already exists)."""
    authors_str = ", ".join(authors) if authors else None
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO articles (site_name, url, title, text, authors, publish_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (site_name, url, title, text, authors_str, publish_date),
        )


def get_articles_by_url(search: str) -> list[dataArticle]:
    """Retrieve all articles whose URL contains the given string."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE url LIKE ? ORDER BY created_at DESC",
            (f"%{search}%",),
        ).fetchall()
    return [dataArticle.from_row(row) for row in rows]

def get_article_by_url(url: str) -> dataArticle | None:
    """Retrieve a single article by its exact URL."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM articles WHERE url = ?",
            (url,),
        ).fetchone()
    return dataArticle.from_row(row) if row else None


def get_processed_urls(search: str) -> set[str]:
    """Return the set of already-saved article URLs that contain the given string."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT url FROM articles WHERE url LIKE ?",
            (f"%{search}%",),
        ).fetchall()
    return {row["url"] for row in rows}


def get_all_articles() -> list[dataArticle]:
    """Return all articles ordered by creation date descending."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY created_at DESC"
        ).fetchall()
    return [dataArticle.from_row(row) for row in rows]


def get_articles_after(date: datetime) -> list[dataArticle]:
    """Return all articles created after the given datetime."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE created_at >= ? ORDER BY created_at DESC",
            (date,),
        ).fetchall()
    return [dataArticle.from_row(row) for row in rows]


def set_score(url: str, score: int, summary: str | None = None) -> None:
    """Set the score and summary for an article by its URL."""
    with _get_connection() as conn:
        conn.execute(
            "UPDATE articles SET score = ?, summary = ? WHERE url = ?",
            (score, summary, url),
        )


def get_unscored_articles() -> list[dataArticle]:
    """Return all articles that have not been scored yet (score = -1)."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE score = -1 ORDER BY created_at DESC"
        ).fetchall()
    return [dataArticle.from_row(row) for row in rows]


# Ensure the table exists on first import
init_db()
