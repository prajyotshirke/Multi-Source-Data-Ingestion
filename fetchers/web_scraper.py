import os
import time
from typing import List

import requests
from bs4 import BeautifulSoup

from fetchers.common import BaseFetcher, NetworkException, ParsingException
from fetchers.models import Article


class WebScraperFetcher(BaseFetcher):
    """
    Fetcher for web scraping (BBC News).

    DESIGN DECISIONS:
    - Target: BBC News
    - Ethics: delay between requests
    - Retry only on network errors, not parsing errors
    """

    BASE_URL = "https://www.bbc.com/news/world/asia/india"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Educational - Portfolio Project) "
            "AppleWebKit/537.36 (KHTML, like Gecko)"
        )
    }

    def __init__(self, max_retries: int = 3):
        super().__init__(max_retries=max_retries)
        self.timeout = int(os.getenv("WEB_SCRAPER_TIMEOUT", 10))

    def fetch(self, max_articles: int = 5) -> List[Article]:
        """
        Scrape BBC News and return normalized Article objects.
        """
        self.logger.info(f"🌐 Scraping BBC News (max: {max_articles})")

        try:
            articles = self._retry_with_backoff(
                self._scrape_articles,
                max_articles=max_articles,
            )
            self.logger.info(f"✅ Got {len(articles)} articles from web scraping")
            return articles

        except Exception as e:
            self.logger.error(f"❌ Web scraping failed: {str(e)}")
            return []

    def _scrape_articles(self, max_articles: int) -> List[Article]:
        """Internal method - called by _retry_with_backoff"""
        try:
            response = requests.get(
                self.BASE_URL,
                headers=self.HEADERS,
                timeout=self.timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            articles: List[Article] = []

            # Primary selector (your original approach)
            article_elements = soup.find_all("h2", {"data-testid": True}, limit=max_articles * 2)

            # Fallback selector
            if not article_elements:
                article_elements = soup.find_all("a", class_="sc-4fedabbc-3", limit=max_articles * 2)

            for element in article_elements[:max_articles]:
                try:
                    title_elem = element.find("span") if hasattr(element, "find") else None
                    if not title_elem:
                        title_elem = element

                    title = title_elem.get_text(strip=True) if title_elem else ""
                    if not title:
                        continue

                    link_elem = element.find_parent("a") if hasattr(element, "find_parent") else None
                    link_elem = link_elem or element
                    url = link_elem.get("href", "") if hasattr(link_elem, "get") else ""

                    if url and not url.startswith("http"):
                        url = f"https://www.bbc.com{url}"

                    content = f"News from BBC India: {title}"

                    article = self._normalize_article(
                        title=title,
                        content=content,
                        source="web",
                        url=url,
                    )
                    articles.append(article)

                    # Ethical delay (NOTE: tests may want this mocked/disabled)
                    time.sleep(1)

                except Exception as e:
                    self.logger.warning(f"Skipping article due to parsing error: {str(e)}")
                    continue

            return articles

        except requests.Timeout:
            raise NetworkException(f"Request timeout ({self.timeout}s)")
        except requests.ConnectionError as e:
            raise NetworkException(f"Connection error: {str(e)}")
        except Exception as e:
            raise ParsingException(f"HTML parsing error: {str(e)}")
