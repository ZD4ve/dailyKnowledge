import logging
logging.basicConfig(level=logging.DEBUG, force=True)

import scrapeSite
scrapeSite.scrape("AP News")

"""
import newspaper
try:
    testSource = newspaper.build('https://economist.com', memorize_articles=False, number_threads=1, http_success_only=True)
except Exception as e:
    print(f"Error building source: {e}")
    exit()

article_urls = [article.url for article in testSource.articles]
for url in article_urls:
    print(url)

articles = testSource.articles[:3]
for article in articles:
    article.download()
    article.parse()
    print('----------------------------------------')
    print(article.title)
    print(article.text[:200])
"""

