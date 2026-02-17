import newspaper
from db import get_processed_urls, save_article
from helper import extract_site_from

def scrape(url: str) -> None:
    '''
    Scrape articles from the given URL and save them to the database if not already processed.
    '''
    source = newspaper.build("https://"+url)
    processed = get_processed_urls(url)
    for article in source.articles:
        if extract_site_from(article.url) != url:
            continue
        if article.url not in processed:
            article.download()
            article.parse()
            save_article(
                url=article.url,
                title=article.title,
                text=article.text,
                authors=article.authors,
                publish_date=article.publish_date,
            )
    