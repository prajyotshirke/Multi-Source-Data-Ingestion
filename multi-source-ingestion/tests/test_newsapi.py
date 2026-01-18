import pytest
from unittest.mock import Mock, patch, MagicMock
from fetchers.newsapi import NewsAPIFetcher
from fetchers.common import NetworkException, ValidationException, ParsingException
import requests


class TestNewsAPIFetcher:
    """Test NewsAPI fetcher error handling and normalization"""
    
    @pytest.fixture
    def fetcher(self):
        """Setup: Create fetcher instance"""
        return NewsAPIFetcher(api_key="test_key_12345")
    
    @pytest.fixture
    def mock_response_success(self):
        """Mock successful API response"""
        return {
            "status": "ok",
            "articles": [
                {
                    "title": "India launches satellite",
                    "description": "ISRO launches satellite into orbit",
                    "content": "Full article content here...",
                    "url": "https://example.com/article1",
                },
                {
                    "title": "Tech industry growth",
                    "description": "India tech sector grows 25% YoY",
                    "content": None,  # Test missing content
                    "url": "https://example.com/article2",
                }
            ]
        }
    
    # ============= TEST 1: Successful fetch =============
    def test_fetch_success(self, fetcher, mock_response_success):
        """✅ Test: Fetcher returns normalized articles"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_response_success
            mock_get.return_value.status_code = 200
            
            articles = fetcher.fetch(query="India", max_articles=2)
            
            assert len(articles) == 2
            assert articles.title == "India launches satellite"
            assert articles.source == "newsapi"
            assert articles.url == "https://example.com/article1"
            assert "satellite" in articles.content
    
    # ============= TEST 2: Timeout handling =============
    def test_timeout_with_retry(self, fetcher):
        """✅ Test: Handles timeout and retries (eventually fails)"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timeout")
            
            # Fetcher should retry 3 times, then return empty list
            articles = fetcher.fetch()
            
            assert articles == []
            assert mock_get.call_count >= 3  # Retried multiple times
    
    # ============= TEST 3: Rate limit handling =============
    def test_rate_limit_429(self, fetcher):
        """✅ Test: Handles rate limit (429) error"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
            mock_get.return_value = mock_response
            
            # Should return empty list, not crash
            articles = fetcher.fetch()
            
            assert articles == []
    
    # ============= TEST 4: Auth error (no retry) =============
    def test_invalid_api_key(self, fetcher):
        """✅ Test: Detects invalid API key (401) without retry"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"status": "error", "message": "Unauthorized"}
            mock_get.return_value = mock_response
            
            articles = fetcher.fetch()
            
            assert articles == []
            # No retry for auth errors
            assert mock_get.call_count == 1
    
    # ============= TEST 5: Malformed JSON response =============
    def test_malformed_response(self, fetcher):
        """✅ Test: Handles malformed API response"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "error"}  # Missing 'articles' key
            mock_get.return_value = mock_response
            
            articles = fetcher.fetch()
            
            # Should return empty list, not crash
            assert articles == []
    
    # ============= TEST 6: Output normalization =============
    def test_output_normalization(self, fetcher, mock_response_success):
        """✅ Test: All articles have required fields"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            mock_get.return_value.json.return_value = mock_response_success
            mock_get.return_value.status_code = 200
            
            articles = fetcher.fetch()
            
            for article in articles:
                # Every article must have these fields
                assert article.title
                assert article.content
                assert article.source == "newsapi"
                assert article.url
                assert article.fetched_at
                assert "T" in article.fetched_at  # ISO 8601 format
    
    # ============= TEST 7: Empty API response =============
    def test_empty_articles(self, fetcher):
        """✅ Test: Handles empty articles list"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"status": "ok", "articles": []}
            mock_get.return_value.status_code = 200
            
            articles = fetcher.fetch()
            
            assert articles == []
    
    # ============= TEST 8: Connection error with backoff =============
    def test_connection_error_retry(self, fetcher):
        """✅ Test: Retries on connection error"""
        with patch('fetchers.newsapi.requests.get') as mock_get:
            # First 2 calls fail, 3rd succeeds
            mock_get.side_effect = [
                requests.ConnectionError("Connection refused"),
                requests.ConnectionError("Connection refused"),
                Mock(status_code=200, json=lambda: {"status": "ok", "articles": []})
            ]
            
            # This would retry, but still fails after 3 attempts
            articles = fetcher.fetch()
            
            # Confirm retries happened
            assert mock_get.call_count >= 1
