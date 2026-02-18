import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from config import get_all_urls
from db import get_all_articles, get_unscored_articles, set_score
from llmRelevance import AsyncRateLimiter, async_estimate, RATE_LIMIT
from scrapeSite import scrape

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


# --- Background tasks ---

def task_scrape_all() -> None:
    """Scrape all sources from config and save new articles to DB."""
    for name, url in get_all_urls():
        logger.info(f"Scraping {name} ({url})")
        scrape(name, url)


async def task_score_unscored() -> None:
    """Score all articles that have not been scored yet."""
    articles = get_unscored_articles()
    if not articles:
        logger.info("No unscored articles.")
        return

    logger.info(f"Scoring {len(articles)} articles...")
    rate_limiter = AsyncRateLimiter(RATE_LIMIT)

    async def process(article):
        result = await async_estimate(article, rate_limiter)
        if result is not None:
            score, summary = result
            set_score(article.url, score, summary)

    await asyncio.gather(*[process(a) for a in articles])
    logger.info("Scoring complete.")


# --- FastAPI app ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Scrape every 10 minutes
    scheduler.add_job(
        task_scrape_all,
        IntervalTrigger(minutes=10),
        id="scrape",
        replace_existing=True,
    )
    # Score unscored articles every 10 minutes (offset slightly)
    scheduler.add_job(
        task_score_unscored,
        IntervalTrigger(minutes=10, seconds=30),
        id="score",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started.")
    yield
    scheduler.shutdown()
    logger.info("Scheduler stopped.")


app = FastAPI(lifespan=lifespan)


# --- API endpoints ---

@app.get("/articles")
def list_articles():
    return get_all_articles()


@app.get("/articles/unscored")
def list_unscored():
    return get_unscored_articles()


@app.post("/run/scrape")
def run_scrape():
    """Manually trigger a scrape of all sources."""
    task_scrape_all()
    return {"status": "ok"}


@app.post("/run/score")
async def run_score():
    """Manually trigger scoring of all unscored articles."""
    await task_score_unscored()
    return {"status": "ok"}


@app.get("/jobs")
def list_jobs():
    """List all scheduled jobs and their next run times."""
    return [
        {"id": job.id, "next_run": str(job.next_run_time)}
        for job in scheduler.get_jobs()
    ]
