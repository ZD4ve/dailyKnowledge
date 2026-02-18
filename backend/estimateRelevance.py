import asyncio
from db import get_unscored_articles,set_score
from helper import dataArticle
from llmRelevance import async_estimate



async def async_process_articles() -> None:
    """Retrieve unscored articles, estimate relevance concurrently, and store in db."""
    articles = get_unscored_articles()
    tasks = [_process(article) for article in articles]
    await asyncio.gather(*tasks, return_exceptions=True)


async def _process(article: dataArticle) -> None:
    if article is None:
        return
    if article.score != -1:
        return  # already scored
    result = await async_estimate(article)
    if result is None:
        print(f"Failed to estimate relevance for URL: {article.url}")
        return
    score, summary = result
    set_score(article.url, score, summary)