from fetchers.newsapi import NewsAPIFetcher
from fetchers.csv_reader import CSVReaderFetcher
from fetchers.web_scraper import WebScraperFetcher
from fetchers.common import Article, save_articles_to_json

all = [
'NewsAPIFetcher',
'CSVReaderFetcher',
'WebScraperFetcher',
'Article',
'save_articles_to_json'
]