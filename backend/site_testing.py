import logging
logging.basicConfig(level=logging.DEBUG)

import newspaper

'''
from playwright_stealth import add_stealth_to_context
from playwright.sync_api import sync_playwright
import time

user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
def getSite(url: str) -> str: 
    # Using Playwright to render JavaScript
    with sync_playwright() as p:
        # Launch with reduced automation flags
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]) 
        # Create a context with a custom user-agent and viewport, then apply stealth init script
        context = browser.new_context(user_agent=user_agent, viewport={"width": 1280, "height": 800})
        add_stealth_to_context(context)
        page = context.new_page()
        page.goto(url)
        time.sleep(3) # Allow the javascript to render
        content = page.content()
        browser.close()
    return content

html = getSite('https://reuters.com/business')
print(html) # Print the first 500 characters of the HTML to verify it was fetched correctly
testSource = newspaper.build('https://reuters.com/business', memoize_articles=False, number_threads=4, input_html=html, http_success_only=True)
'''

try:
    testSource = newspaper.build('https://economist.com', memoize_articles=True, number_threads=1, http_success_only=True)
except Exception as e:
    print(f"Error building source: {e}")
    exit()

print("---root+not in path:-------------------------------")
article_urls = [article.url for article in testSource.articles]
for url in article_urls:
    print(url)

#print(len(article_urls))
#testSource.generate_articles(limit=100)

#articles = testSource.download_articles()

#print(len(articles))
#print([article.url for article in articles])

articles = testSource.articles[:3]
for article in articles:
    article.download()
    article.parse()
    print('------------------')
    print(article.title)
    print(article.summary)
    #print(article.text[:300])
    

 