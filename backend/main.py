import asyncio
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from config import get_all_urls, get_sites_by_category
import db 
from estimateRelevance import async_process_articles
from scrapeSite import scrape
import config


logging.basicConfig(level=logging.INFO)
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
    logger.info("Scoring unscored articles...")
    await async_process_articles()


# --- FastAPI app ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        task_scrape_all,
        IntervalTrigger(minutes=30, start_date=datetime.now()+timedelta(minutes=1)),
        id="scrape",
        replace_existing=True,
    )
    scheduler.add_job(
        task_score_unscored,
        IntervalTrigger(minutes=60, start_date=datetime.now()+timedelta(minutes=11)),
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
    return db.get_all_articles()

@app.get("/categories")
def list_categories():
    return config.get_categories()

@app.get("/categories/{category}")
def list_sites_by_category(category: str):
    return get_sites_by_category(category)

@app.get("/categories/{category}/articles")
def list_articles_by_category(category: str):
    sites = get_sites_by_category(category)
    articles = []
    for site in sites:
        articles.extend(db.get_articles_by_site(site))
    # Sort articles by publish_date descending
    articles.sort(key=lambda a: a.publish_date, reverse=True)
    return articles

@app.get("/articles/{category}/{site_name}")
def list_articles_by_site(category: str, site_name: str):
    return db.get_articles_by_site(site_name)

@app.get("/today")
def list_today_articles():
    today = datetime.now().date()
    return db.get_articles_after(datetime(today.year, today.month, today.day))

@app.get("/today/minscore/{min_score}")
def list_today_articles_by_score(min_score: int):
    today = datetime.now().date()
    return db.get_articles_by_score_after(min_score, datetime(today.year, today.month, today.day))

@app.get("/scrape")
def trigger_scrape():
    task_scrape_all()
    return {"message": "Scraping triggered"}

@app.get("/score")
async def trigger_score():
    await task_score_unscored()
    return {"message": "Scoring triggered"}