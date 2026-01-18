# fetchers/newsapi.py
import requests
from typing import List
from fetchers.common import BaseFetcher, NetworkException, ParsingException
from fetchers.models import Article
import os


class NewsAPIFetcher(BaseFetcher):
    """
    Fetcher for NewsAPI (https://newsapi.org/) 
    DESIGN DECISIONS:
    - NewsAPI provides normalized JSON response (easier parsing)
    - Rate limits: 100 requests/day free tier (acceptable for portfolio)
    - Error handling: Separate retry logic for timeouts vs auth errors
    - Graceful degradation: If API fails, just log and return empty list
    """

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str = None, max_retries: int = 3):
        super().__init__(max_retries=max_retries)
        self.api_key = api_key or os.getenv("NEWSAPI_API_KEY")
        self.timeout = int(os.getenv("NEWSAPI_TIMEOUT", 10))
        
        if not self.api_key:
            raise ValueError("NEWSAPI_API_KEY not found in environment variables")

    def fetch(self, query: str = "India", max_articles: int = 10) -> List[Article]:
        """
        Fetch articles from NewsAPI.
        
        STRATEGY:
        - Use retry_with_backoff for network errors
        - Catch auth errors separately (permanent, no retry)
        - Return empty list if source fails (don't crash pipeline)
        """
        self.logger.info(f"📡 Fetching from NewsAPI (query: '{query}', max: {max_articles})")
        
        try:
            articles = self._retry_with_backoff(
                self._fetch_from_api,
                query=query,
                max_articles=max_articles
            )
            self.logger.info(f"✅ Got {len(articles)} articles from NewsAPI")
            return articles
        
        except Exception as e:
            self.logger.error(f"❌ NewsAPI fetching failed: {str(e)}")
            return []  # Return empty list instead of crashing

    def _fetch_from_api(self, query: str, max_articles: int) -> List[Article]:
        """Internal method - called by _retry_with_backoff"""
        
        try:
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": max_articles,
                "apiKey": self.api_key
            }
            
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise ValueError("Invalid API key (401 Unauthorized)")
            if response.status_code == 429:
                raise NetworkException("Rate limit exceeded (429)")
            if response.status_code >= 500:
                raise NetworkException(f"Server error ({response.status_code})")
            
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "ok":
                raise ParsingException(f"API error: {data.get('message', 'Unknown error')}")
            
            articles = []
            for item in data.get("articles", []):
                try:
                    # NewsAPI returns: title, description, content, url
                    # Use description as content preview since full content is behind paywall
                    article = self._normalize_article(
                        title=item.get("title", ""),
                        content=item.get("description") or item.get("content") or "No content available",
                        source="newsapi",
                        url=item.get("url", "")
                    )
                    articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Skipping article due to error: {str(e)}")
                    continue
            
            return articles
        
        except requests.Timeout:
            raise NetworkException(f"Request timeout ({self.timeout}s)")
        except requests.ConnectionError as e:
            raise NetworkException(f"Connection error: {str(e)}")
        except Exception as e:
            raise ParsingException(f"Unexpected error: {str(e)}")
