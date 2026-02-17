import time
from tqdm import tqdm
from config import get_all_urls
from scrapeSite import scrape
from db import get_articles_by_url
from estimateUsefullness import estimate

RATE_LIMIT = 15  # requests per minute
DELAY = 60 / RATE_LIMIT 

# 1. Scrape the first site from config
first_url = get_all_urls()[0]
#print(f"Scraping {first_url}...")
#scrape(first_url)

# 2. Get all stored articles
articles = get_articles_by_url(first_url)[:20]
print(f"Scoring {len(articles)} articles...\n")

# 3. Score each article with progress bar (throttled to stay within rate limit)
results = []
for i, a in enumerate(tqdm(articles, desc="Estimating relevance")):
    start = time.time()
    score = estimate(a)
    results.append((score, a["title"], a["url"]))
    elapsed = time.time() - start
    remaining = DELAY - elapsed
    if i < len(articles) - 1 and remaining > 0:
        time.sleep(remaining)

# 4. Print sorted by relevance (highest first)
results.sort(key=lambda x: x[0] if x[0] is not None else -1, reverse=True)
for score, title, url in results:
    print(f"[{score}] {title}\n    {url}\n")


#TODO: ASYNC IMPLEMENTATION USING THREADING OR ASYNCIO TO HANDLE MULTIPLE ARTICLES IN PARALLEL WHILE RESPECTING RATE LIMIT
#maybe use this as a reference: https://medium.com/@Aman-tech/how-make-async-calls-to-openais-api-cfc35f252ebd