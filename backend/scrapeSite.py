import logging

import newspaper
from config import get_filter
from db import get_processed_urls, save_article

logger = logging.getLogger(__name__)

def scrape(site_name: str, url: str) -> None:
    """
    Scrape articles from the given URL and save them to the database
    if not already processed. Uses Newspaper4k bulk download.
    """
    logging.info(f"Scraping {site_name}...")

    try:
        source = newspaper.build(url, memorize_articles=True, number_threads=4)
    except Exception as e:
        logger.error(f"Error building newspaper source for {url}: {e}")
        return

    #Filtering
    filter = set(get_filter(site_name) or [])
    filter.add(url)
    processed = set(get_processed_urls(url))
    articles_to_download = [
        article for article in source.articles
        if any(keyword in article.url for keyword in filter)
        and article.url not in processed
    ]
    if not articles_to_download:
        return
    source.articles = articles_to_download


    try:
        source.download_articles()
        source.parse_articles()
    except Exception as e:
        logger.error(f"Error downloading/parsing articles from {url}: {e}")
        return


    for article in source.articles:
        if not article.is_parsed or not article.text:
            continue
        save_article(
            site_name=site_name,
            url=article.url,
            title=article.title,
            text=article.text,
            authors=article.authors,
            publish_date=article.publish_date,
        )
    
    logging.info(f"Finished scraping {site_name}. {len(source.articles)} articles downloaded.")
