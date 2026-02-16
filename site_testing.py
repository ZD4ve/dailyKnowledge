import newspaper

testSource = newspaper.build('https://telex.hu/')#, language='hu'
print(testSource.category_urls())

#article_urls = [article.url for article in testSource.articles]
#print(article_urls)
#print(len(article_urls))
#testSource.generate_articles(limit=100)

#articles = testSource.download_articles()

#print(len(articles))
#print([article.url for article in articles])

articles = testSource.articles[:3]
for article in articles:
    article.download()
    article.parse()
    article.nlp()
    print('------------------')
    print(article.title)
    print(article.summary)
    #print(article.text[:300])