import asyncio
import os
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
        IntervalTrigger(minutes=60, start_date=datetime.now()+timedelta(minutes=1)),
        id="scrape",
        replace_existing=True,
    )
    scheduler.add_job(
        task_score_unscored,
        IntervalTrigger(minutes=60, start_date=datetime.now()+timedelta(minutes=31)),
        id="score",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started.")
    yield
    scheduler.shutdown()
    logger.info("Scheduler stopped.")


app = FastAPI(lifespan=lifespan)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# --- API endpoints ---
api_router = APIRouter(prefix="/api")

@api_router.get("/categories")
def list_categories():
    return config.get_categories()

@api_router.get("/categories/{category}/articles")
def list_articles_by_category(category: str):
    sites = get_sites_by_category(category)
    articles = []
    for site in sites:
        articles.extend(db.get_articles_by_site(site))
    articles.sort(key=lambda a: a.score, reverse=True)
    return articles 



app.include_router(api_router)