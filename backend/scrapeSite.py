import logging

import newspaper
from newspaper.source import Feed
import config
from db import get_stored_urls, save_article

logger = logging.getLogger(__name__)

def scrape(site_name: str) -> None:
    """
    Scrape articles from the given URL and save them to the database
    if not already processed. Uses Newspaper4k bulk download.
    """

    url = config.get_url(site_name)
    if not url:
        logger.error(f"No URL found for site '{site_name}' in config.")
        return
    rss = config.get_rss(site_name)
    logging.info(f"Scraping {site_name} using {"rss" if rss else "crawler"}...")


    try:
        source = newspaper.build("https://"+url, memorize_articles=True, number_threads=(1 if rss is not None else 4), dry=(rss is not None), http_success_only=True)
        if rss is not None:
            source.feeds = [Feed(url=url) for url in rss]
            source.download_feeds()
            source.generate_articles()
    except Exception as e:
        logger.error(f"Error building newspaper source for {url}: {e}")
        return

    #Filtering
    filter = set(config.get_filter(site_name) or [])
    stored = set(get_stored_urls(url))
    articles_to_download = [
        article for article in source.articles
        if any(keyword in article.url for keyword in filter)
        and (url in article.url)
        and article.url not in stored
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