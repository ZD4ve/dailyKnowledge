"""
Database layer supporting both SQLite (local dev) and PostgreSQL (production).

Set DATABASE_URL to a PostgreSQL connection string to use Postgres, e.g.:
  DATABASE_URL=postgresql://user:password@host:5432/dbname

Leave DATABASE_URL unset (or set it to a sqlite:// path) to use SQLite locally.
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from helper import dataArticle

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
SQLITE_PATH: str = os.getenv("SQLITE_PATH", "articles.db")


def _is_postgres() -> bool:
    return DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")


def _ph() -> str:
    """Return the SQL placeholder for the active backend."""
    return "%s" if _is_postgres() else "?"


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

@contextmanager
def _get_cursor():
    """
    Yield a (connection, cursor) pair that works for both SQLite and PostgreSQL.
    Commits on success, rolls back on error, closes the connection on exit.
    The cursor always returns rows as plain dicts.
    """
    if _is_postgres():
        import psycopg2 # pyright: ignore[reportMissingModuleSource]
        import psycopg2.extras # pyright: ignore[reportMissingModuleSource]

        conn = psycopg2.connect(DATABASE_URL)
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    yield cur
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                class _DictCursor:
                    """Thin wrapper that makes sqlite3 cursor results look like dicts."""
                    def __init__(self, connection: sqlite3.Connection):
                        self._conn = connection
                        self._cur: sqlite3.Cursor | None = None

                    def execute(self, sql: str, params: tuple = ()) -> "_DictCursor":
                        self._cur = self._conn.execute(sql, params)
                        return self

                    def fetchall(self) -> list[dict]:
                        return [dict(r) for r in (self._cur.fetchall() if self._cur else [])]

                    def fetchone(self) -> dict | None:
                        row = self._cur.fetchone() if self._cur else None
                        return dict(row) if row else None

                yield _DictCursor(conn)
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create the articles table if it doesn't exist."""
    p = _ph()
    if _is_postgres():
        ddl = """
            CREATE TABLE IF NOT EXISTS articles (
                id          SERIAL PRIMARY KEY,
                site_name   TEXT,
                url         TEXT UNIQUE NOT NULL,
                title       TEXT,
                text        TEXT,
                authors     TEXT,
                publish_date TIMESTAMP,
                score       INTEGER DEFAULT -1,
                summary     TEXT DEFAULT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    else:
        ddl = """
            CREATE TABLE IF NOT EXISTS articles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                site_name   TEXT,
                url         TEXT UNIQUE NOT NULL,
                title       TEXT,
                text        TEXT,
                authors     TEXT,
                publish_date TIMESTAMP,
                score       INTEGER DEFAULT -1,
                summary     TEXT DEFAULT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    with _get_cursor() as cur:
        cur.execute(ddl)


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def save_article(site_name: str, url: str, title: str, text: str,
                 authors: list[str] | None = None,
                 publish_date: datetime | None = None) -> None:
    """Save a single article to the database (skip if URL already exists)."""
    authors_str = ", ".join(authors) if authors else None
    p = _ph()
    if _is_postgres():
        sql = f"""
            INSERT INTO articles (site_name, url, title, text, authors, publish_date)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
            ON CONFLICT (url) DO NOTHING
        """
    else:
        sql = f"""
            INSERT OR IGNORE INTO articles (site_name, url, title, text, authors, publish_date)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
        """
    with _get_cursor() as cur:
        cur.execute(sql, (site_name, url, title, text, authors_str, publish_date))


def set_score(url: str, score: int, summary: str | None = None) -> None:
    """Set the score and summary for an article by its URL."""
    p = _ph()
    with _get_cursor() as cur:
        cur.execute(
            f"UPDATE articles SET score = {p}, summary = {p} WHERE url = {p}",
            (score, summary, url),
        )


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_articles_by_url(search: str) -> list[dataArticle]:
    """Retrieve all articles whose URL contains the given string."""
    p = _ph()
    with _get_cursor() as cur:
        cur.execute(
            f"SELECT * FROM articles WHERE url LIKE {p} ORDER BY created_at DESC",
            (f"%{search}%",),
        )
        rows = cur.fetchall()
    return [dataArticle.from_row(row) for row in rows]


def get_articles_by_site(site_name: str) -> list[dataArticle]:
    """Retrieve all articles from a specific site."""
    p = _ph()
    with _get_cursor() as cur:
        cur.execute(
            f"SELECT * FROM articles WHERE site_name = {p} ORDER BY created_at DESC",
            (site_name,),
        )
        rows = cur.fetchall()
    return [dataArticle.from_row(row) for row in rows]

_SHUFFLE_SEED = 42

def get_articles_by_sites_paginated(
    site_names: list[str],
    since: str | None,
    until: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dataArticle], int]:
    """Retrieve paginated articles for a list of sites with optional date filters.

    Scored articles (score != -1) are returned first, ordered by score DESC.
    Articles with the same score are ordered pseudo-randomly using _SHUFFLE_SEED
    as a tiebreaker, giving a stable non-ID-order shuffle.
    Unscored articles (score = -1) appear last.
    Returns a (articles, total) tuple where total is the count before pagination.
    """
    if not site_names:
        return [], 0

    p = _ph()
    in_placeholders = ", ".join(p for _ in site_names)
    params: list = list(site_names)

    where_clauses = [f"site_name IN ({in_placeholders})"]
    if since:
        where_clauses.append(f"publish_date >= {p}")
        params.append(since)
    if until:
        where_clauses.append(f"publish_date < {p}")
        params.append(until)

    where_sql = " AND ".join(where_clauses)
    # Tiebreaker: Knuth multiplicative hash spreads sequential IDs far apart,
    # giving a stable pseudo-random shuffle within the same score group.
    order_sql = f"ORDER BY CASE WHEN score = -1 THEN 1 ELSE 0 END ASC, score DESC, (id * 2654435761 + {_SHUFFLE_SEED}) % 999983"

    count_sql = f"SELECT COUNT(*) AS cnt FROM articles WHERE {where_sql}"
    data_sql = (
        f"SELECT * FROM articles WHERE {where_sql} "
        f"{order_sql} LIMIT {p} OFFSET {p}"
    )

    with _get_cursor() as cur:
        cur.execute(count_sql, tuple(params))
        count_row = cur.fetchone()
        total = count_row["cnt"] if count_row else 0

        cur.execute(data_sql, tuple(params + [limit, offset]))
        rows = cur.fetchall()

    return [dataArticle.from_row(row) for row in rows], total


def get_unscored_articles() -> list[dataArticle]:
    """Return all articles that have not been scored yet (score = -1)."""
    with _get_cursor() as cur:
        cur.execute(
            "SELECT * FROM articles WHERE score = -1 ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
    return [dataArticle.from_row(row) for row in rows]

def get_stored_urls(search: str) -> set[str]:
    """Return the set of already-saved article URLs that contain the given string."""
    p = _ph()
    with _get_cursor() as cur:
        cur.execute(
            f"SELECT url FROM articles WHERE url LIKE {p}",
            (f"%{search}%",),
        )
        rows = cur.fetchall()
    return {row["url"] for row in rows}


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
def delete_old(date: datetime) -> None:
    """Delete all articles published or created before the given date."""
    p = _ph()
    with _get_cursor() as cur:
        cur.execute(
            f"DELETE FROM articles WHERE publish_date < {p} OR created_at < {p}",
            (date, date),
        )


# Ensure the table exists on first import
init_db()
