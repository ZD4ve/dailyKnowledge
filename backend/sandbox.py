import asyncio
from tqdm.asyncio import tqdm as atqdm
from config import get_all_urls
from scrapeSite import scrape
from db import get_articles_by_url
from estimateUsefullness import async_estimate, AsyncRateLimiter

RATE_LIMIT = 15  # requests per minute

# 1. Scrape the first site from config
first_name, first_url = get_all_urls()[0]
#print(f"Scraping {first_name} ({first_url})...")
scrape(first_name, first_url)

# 2. Get all stored articles
articles = get_articles_by_url(first_url)
print(f"Scoring {len(articles)} articles...\n")


async def main():
    rate_limiter = AsyncRateLimiter(RATE_LIMIT)

    # 3. Fire off all tasks — rate limiter handles spacing
    async def process(article: dict) -> tuple | None:
        result = await async_estimate(article, rate_limiter)
        if result is None:
            return None
        score, summary = result
        return score, summary, article["title"], article["url"]

    tasks = [process(a) for a in articles]
    results = []
    for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Estimating relevance"):
        result = await coro
        if result is not None:
            results.append(result)

    # 4. Print sorted by relevance (highest first)
    results.sort(key=lambda x: x[0], reverse=True)
    for score, summary, title, url in results:
        print(f"[{score}] {title}\n    {summary}\n    {url}\n")


asyncio.run(main())