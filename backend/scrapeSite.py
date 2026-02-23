import logging

import newspaper
from newspaper.source import Feed
from newspaper.google_news import GoogleNewsSource
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
    google = config.get_google(site_name)
    logging.info(f"Scraping {site_name} using {"rss" if rss else "google" if google else "crawler"}...")

    news_config = newspaper.Config()
    news_config.memoize_articles = False
    news_config.number_threads = 1 if rss or google else 4
    news_config.http_success_only = True
    news_config.min_word_count = 250

    try:
        if google:
            source = GoogleNewsSource(period="3h", max_results=50)
            source.build(site=google)
            source.config = news_config
        else:
            source = newspaper.build("https://"+url, config=news_config,  dry=(rss is not None))
            if rss is not None:
                source.feeds = [Feed(url=url) for url in rss]
                tmp = source.download_feeds()
                source.generate_articles()
    except Exception as e:
        logger.error(f"Error building newspaper source for {url}: {e}")
        return

    #Filtering
    filter = set(config.get_filter(site_name) or [""])
    stored = set(get_stored_urls(url))
    articles = [article for article in source.articles]
    articles_to_download = [
        article for article in articles
        if any(keyword in article.url for keyword in filter)
        and (url in article.url)
        and article.url not in stored
    ]
    logger.info(f"Found {len(articles)} articles for {site_name}, {len(articles_to_download)} to download after filtering and deduplication.")
    if articles_to_download is None or len(articles_to_download) == 0:
        return
    source.articles = articles_to_download

    # Downloading
    try:
        source.download_articles()
        if not google:
            source.parse_articles()
        else:
            for article in source.articles: 
                article.parse()
    except Exception as e:
        logger.error(f"Error downloading/parsing articles from {url}: {e}")
        return

    counter = 0
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
        counter += 1
    
    logging.info(f"Finished scraping {site_name}. {counter} articles downloaded.")