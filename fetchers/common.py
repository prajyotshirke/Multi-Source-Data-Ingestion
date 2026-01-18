import logging
import time
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
from fetchers.models import Article
import os
from datetime import datetime, timezone


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class FetcherException(Exception):
    """Base exception for fetcher errors"""
    pass


class NetworkException(FetcherException):
    """Network-related errors (timeout, connection refused)"""
    pass


class ParsingException(FetcherException):
    """Data parsing errors (malformed JSON, bad CSV)"""
    pass


class ValidationException(FetcherException):
    """Data validation errors (missing required fields)"""
    pass


class BaseFetcher(ABC):
    """
    Abstract base class for all data fetchers.
    Ensures every fetcher implements the fetch() method and returns normalized Article objects
    
    DESIGN: This is the "interface contract" - ensures any new fetcher follows same pattern.
    REUSABILITY: New sources only need to extend this class and implement fetch().
    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 2, timeout: int = 10):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch(self) -> List[Article]:
        """
        Fetch data from source and return normalized Article objects.
        Every fetcher MUST implement this.
        """
        pass

    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """
        Generic retry logic with exponential backoff.
        STRATEGY: Only retry on transient errors (network), not permanent (auth, file not found).
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except NetworkException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed. "
                        f"Retrying in {wait_time}s... Error: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed. Giving up.")
        
        raise last_exception

    def _normalize_article(self, title: str, content: str, source: str, url: str = "N/A") -> Article:
        """
        Normalize raw data into Article schema.
        STRATEGY: Validate early, fail with clear error messages.
        """
        try:
            if not title or len(title.strip()) == 0:
                raise ValidationException("Article title cannot be empty")
            
            if not content or len(content.strip()) == 0:
                raise ValidationException("Article content cannot be empty")
            
            Article.validate_source(source)
            
            article = Article(
                title=title.strip(),
                content=content.strip(),
                source=source,
                url=url or "N/A",
                fetched_at=datetime.now(timezone.utc).isoformat()
            )
            return article
        
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise ValidationException(f"Failed to normalize article: {str(e)}")


def save_articles_to_json(articles: List[Article], output_path: str):
    """
    Save list of Article objects to JSON file.
    DESIGN: Separated concern - writing is independent of fetching.
    """
    try:
        # Extract directory path
        output_dir = os.path.dirname(output_path)

        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([article.to_dict() for article in articles], f, indent=2, ensure_ascii=False)
    
        logging.info(f"✅ Saved {len(articles)} articles to {output_path}")
        return True

    except Exception as e:
        logging.error(f"❌ Failed to save articles to JSON: {str(e)}")
        raise FetcherException(f"JSON save failed: {str(e)}")
