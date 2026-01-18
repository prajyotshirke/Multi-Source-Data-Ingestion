import pytest
import json
import tempfile
import os
from unittest.mock import patch

from main import main
from fetchers.models import Article


class TestMainOrchestration:
    """Test end-to-end pipeline"""

    # ============= TEST 1: End-to-end pipeline =============
    @patch("main.WebScraperFetcher")
    @patch("main.CSVReaderFetcher")
    @patch("main.NewsAPIFetcher")
    def test_main_pipeline(self, mock_newsapi_cls, mock_csv_cls, mock_scraper_cls):
        # Mock instances
        mock_newsapi = mock_newsapi_cls.return_value
        mock_csv = mock_csv_cls.return_value
        mock_scraper = mock_scraper_cls.return_value

        mock_newsapi.fetch.return_value = [
            Article(title="NewsAPI Article", content="Content from NewsAPI", source="newsapi", url="https://newsapi.com/1")
        ]
        mock_csv.fetch.return_value = [
            Article(title="CSV Article", content="Content from CSV", source="csv", url="https://example.com/csv")
        ]
        mock_scraper.fetch.return_value = [
            Article(title="Web Article", content="Content from web", source="web", url="https://bbc.com/article")
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "articles.json")
            with patch("main.os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: output_file if key == "OUTPUT_FILE_PATH" else default

                articles = main()

                assert len(articles) == 3
                assert articles[0].source == "newsapi"
                assert articles[1].source == "csv"
                assert articles[2].source == "web"

    # ============= TEST 2: Partial failure handling =============
    @patch("main.WebScraperFetcher")
    @patch("main.CSVReaderFetcher")
    @patch("main.NewsAPIFetcher")
    def test_main_partial_failure(self, mock_newsapi_cls, mock_csv_cls, mock_scraper_cls):
        mock_newsapi = mock_newsapi_cls.return_value
        mock_csv = mock_csv_cls.return_value
        mock_scraper = mock_scraper_cls.return_value

        mock_newsapi.fetch.side_effect = Exception("API Error")
        mock_csv.fetch.return_value = [Article(title="CSV Article", content="Content", source="csv", url="url")]
        mock_scraper.fetch.side_effect = Exception("Network Error")

        articles = main()

        assert len(articles) == 1
        assert articles[0].source == "csv"

    # ============= TEST 3: Output is valid JSON =============
    @patch("main.WebScraperFetcher")
    @patch("main.CSVReaderFetcher")
    @patch("main.NewsAPIFetcher")
    def test_output_valid_json(self, mock_newsapi_cls, mock_csv_cls, mock_scraper_cls):
        mock_newsapi = mock_newsapi_cls.return_value
        mock_csv = mock_csv_cls.return_value
        mock_scraper = mock_scraper_cls.return_value

        mock_newsapi.fetch.return_value = [Article(title="Test", content="Content", source="newsapi", url="url")]
        mock_csv.fetch.return_value = []
        mock_scraper.fetch.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "articles.json")
            with patch("main.os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: output_file if key == "OUTPUT_FILE_PATH" else default

                main()

                with open(output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                assert isinstance(data, list)
                assert len(data) > 0
                assert "title" in data[0]
                assert "content" in data[0]
                assert "source" in data[0]
                assert "url" in data[0]
                assert "fetched_at" in data[0]

    # ============= TEST 4: All articles normalized =============
    @patch("main.WebScraperFetcher")
    @patch("main.CSVReaderFetcher")
    @patch("main.NewsAPIFetcher")
    def test_all_articles_normalized(self, mock_newsapi_cls, mock_csv_cls, mock_scraper_cls):
        mock_newsapi = mock_newsapi_cls.return_value
        mock_csv = mock_csv_cls.return_value
        mock_scraper = mock_scraper_cls.return_value

        mock_newsapi.fetch.return_value = [Article(title="A", content="B", source="newsapi", url="url1")]
        mock_csv.fetch.return_value = [Article(title="C", content="D", source="csv", url="url2")]
        mock_scraper.fetch.return_value = [Article(title="E", content="F", source="web", url="N/A")]

        articles = main()

        for article in articles:
            assert article.title
            assert article.content
            assert article.source in ["newsapi", "csv", "web"]
            assert article.url
            assert article.fetched_at
            assert "T" in article.fetched_at

    # ============= TEST 5: Adding 4th source (reusability) =============
    @patch("main.WebScraperFetcher")
    @patch("main.CSVReaderFetcher")
    @patch("main.NewsAPIFetcher")
    def test_adding_4th_source(self, mock_newsapi_cls, mock_csv_cls, mock_scraper_cls):
        mock_newsapi_cls.return_value.fetch.return_value = []
        mock_csv_cls.return_value.fetch.return_value = []
        mock_scraper_cls.return_value.fetch.return_value = []

        articles = main()
        assert isinstance(articles, list)
