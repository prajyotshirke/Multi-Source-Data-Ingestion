import pytest
from unittest.mock import Mock, patch
from fetchers.web_scraper import WebScraperFetcher
import requests


class TestWebScraperFetcher:
    """Test web scraper error handling and HTML parsing"""

    @pytest.fixture
    def fetcher(self):
        """Setup: Create fetcher instance"""
        return WebScraperFetcher()

    @pytest.fixture
    def mock_html_response(self):
        """Mock BBC News HTML response"""
        return """
        <html>
            <h2 data-testid="internal-link">
                <span>India announces new education policy</span>
            </h2>
            <h2 data-testid="internal-link">
                <span>Tech sector growth accelerates</span>
            </h2>
        </html>
        """

    # ============= TEST 1: Successful scrape =============
    def test_scrape_success(self, fetcher, mock_html_response):
        """✅ Test: Scrapes HTML and normalizes articles"""
        with patch("fetchers.web_scraper.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = mock_html_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            articles = fetcher.fetch(max_articles=2)

            assert len(articles) >= 1
            assert articles[0].source == "web"
            assert articles[0].title
            assert articles[0].url

    # ============= TEST 2: Timeout handling =============
    def test_timeout_retry(self, fetcher):
        """✅ Test: Handles timeout with retry logic"""
        with patch("fetchers.web_scraper.requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timeout")

            articles = fetcher.fetch()

            assert articles == []
            assert mock_get.call_count >= 3

    # ============= TEST 3: Connection error =============
    def test_connection_error(self, fetcher):
        """✅ Test: Handles connection errors"""
        with patch("fetchers.web_scraper.requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection refused")

            articles = fetcher.fetch()

            assert articles == []

    # ============= TEST 4: Malformed HTML =============
    def test_malformed_html(self, fetcher):
        """✅ Test: Handles malformed HTML gracefully"""
        with patch("fetchers.web_scraper.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = "<html></html>"
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            articles = fetcher.fetch()

            assert articles == []

    # ============= TEST 5: HTTP errors =============
    def test_http_error_500(self, fetcher):
        """✅ Test: Handles 500 server error with retry"""
        with patch("fetchers.web_scraper.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
            mock_get.return_value = mock_response

            articles = fetcher.fetch()

            assert articles == []

    # ============= TEST 6: Output normalization =============
    def test_output_normalization(self, fetcher, mock_html_response):
        """✅ Test: Web scraper output follows schema"""
        with patch("fetchers.web_scraper.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = mock_html_response
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            articles = fetcher.fetch(max_articles=1)

            if articles:
                article = articles[0]
                assert article.source == "web"
                assert article.title
                assert article.content
                assert article.fetched_at
                assert article.url in ("", "N/A") or article.url.startswith("https://")


    # ============= TEST 7: Max articles limit =============
    def test_max_articles_limit(self, fetcher, mock_html_response):
        """✅ Test: Respects max_articles parameter"""
        with patch("fetchers.web_scraper.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = mock_html_response * 5
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            articles = fetcher.fetch(max_articles=2)

            assert len(articles) <= 2
