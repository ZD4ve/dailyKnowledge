import newspaper

testSource = newspaper.build('https://telex.hu/', memoize_articles=False, only_in_path=False)

#print("---root+not in path:-------------------------------")
#article_urls = [article.url for article in testSource.articles]
#for url in article_urls:
#    print(url)


print("---root+only in path:-------------------------------")
testSource = newspaper.build('https://telex.hu/', memoize_articles=False, only_in_path=True)
article_urls = [article.url for article in testSource.articles]
for url in article_urls:
    print(url)

print("---belfold+not in path:-------------------------------")
testSource = newspaper.build('https://telex.hu/belfold/', memoize_articles=False, only_in_path=False)
article_urls = [article.url for article in testSource.articles]
for url in article_urls:
    print(url)

print("---belfold+only in path:-------------------------------")
testSource = newspaper.build('https://telex.hu/belfold/', memoize_articles=False, only_in_path=True)
article_urls = [article.url for article in testSource.articles]
for url in article_urls:
    print(url)

#print(len(article_urls))
#testSource.generate_articles(limit=100)

#articles = testSource.download_articles()

#print(len(articles))
#print([article.url for article in articles])
"""
articles = testSource.articles[:3]
for article in articles:
    article.download()
    article.parse()
    article.nlp()
    print('------------------')
    print(article.title)
    print(article.summary)
    #print(article.text[:300])
"""

    