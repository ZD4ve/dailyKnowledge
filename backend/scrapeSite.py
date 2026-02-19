import newspaper
from db import get_processed_urls, save_article
from helper import extract_site_from


def scrape(site_name: str, url: str) -> None:
    """
    Scrape articles from the given URL and save them to the database
    if not already processed. Uses Newspaper4k bulk download.
    """

    base_url = f"https://{extract_site_from(url)}"
    source = newspaper.build(base_url, memorize_articles=False, number_threads=4)

    #Filtering
    filter1 = f"https://{url}"
    filter2 = f"https://www.{url}"
    processed = set(get_processed_urls(url))
    articles_to_download = [
        article for article in source.articles
        if (article.url.startswith(filter1) or article.url.startswith(filter2))
        and article.url not in processed
    ]
    if not articles_to_download:
        return
    source.articles = articles_to_download


    source.download_articles()
    source.parse_articles()


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
