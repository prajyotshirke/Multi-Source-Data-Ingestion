import os
import logging
from dotenv import load_dotenv

from fetchers.newsapi import NewsAPIFetcher
from fetchers.csv_reader import CSVReaderFetcher
from fetchers.web_scraper import WebScraperFetcher
from fetchers.common import save_articles_to_json

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main(newsapi_fetcher=None, csv_fetcher=None, scraper_fetcher=None):
    output_path = os.getenv("OUTPUT_FILE_PATH", "output/articles.json")
    all_articles = []

    # Instantiate only if not injected
    if newsapi_fetcher is None:
        try:
            newsapi_fetcher = NewsAPIFetcher(api_key=os.getenv("NEWSAPI_API_KEY"))
        except Exception:
            newsapi_fetcher = None

    if csv_fetcher is None:
        csv_fetcher = CSVReaderFetcher()

    if scraper_fetcher is None:
        scraper_fetcher = WebScraperFetcher()

    # NewsAPI
    try:
        if newsapi_fetcher is not None:
            all_articles.extend(newsapi_fetcher.fetch(query="India", max_articles=5))
    except Exception as e:
        logger.error(f"Failed: {str(e)}")

    # CSV
    try:
        all_articles.extend(csv_fetcher.fetch())
    except Exception as e:
        logger.error(f"Failed: {str(e)}")

    # Web Scraper
    try:
        all_articles.extend(scraper_fetcher.fetch(max_articles=3))
    except Exception as e:
        logger.error(f"Failed: {str(e)}")

    # Save output
    if all_articles:
        save_articles_to_json(all_articles, output_path)

    return all_articles


if __name__ == "__main__":
    main()
