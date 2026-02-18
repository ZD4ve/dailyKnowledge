from db import get_article_by_url, get_articles_by_url, set_score
from llmRelevance import async_estimate



async def async_process_article(url: str) -> None:
    """retrieve article with given url, estimate relevance, and store in db"""
    article = get_article_by_url(url)
    if article is None:
        raise ValueError(f"No article found in db with URL: {url}")
    if article.score != -1:
        return  # already scored
    
    result = await async_estimate(article)
    
    if result is None:
        print(f"Failed to estimate relevance for URL: {url}")
        return

    score, summary = result
    set_score(url, score, summary)