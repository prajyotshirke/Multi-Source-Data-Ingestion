import csv
import os
from typing import List

from fetchers.common import BaseFetcher, ParsingException
from fetchers.models import Article


class CSVReaderFetcher(BaseFetcher):
    """
    Fetcher for CSV files (local data source).

    DESIGN DECISIONS:
    - No retry logic needed (file I/O, not network)
    - Graceful error handling: skip bad rows, log why
    - Supports multiple encodings (utf-8, latin-1)
    - STRATEGY: If file missing → return empty list (don't crash pipeline)
    """

    def __init__(self, file_path: str = None):
        super().__init__()
        self.file_path = file_path or os.getenv("CSV_FILE_PATH", "sample_data.csv")

    def fetch(self) -> List[Article]:
        """
        Read CSV file and return normalized Article objects.

        STRATEGY:
        - If file missing, return empty list (log warning)
        - If file is unreadable, try different encoding
        - Skip bad rows
        """
        self.logger.info(f"📄 Reading CSV from {self.file_path}")

        if not os.path.exists(self.file_path):
            self.logger.warning(f"CSV file not found: {self.file_path}")
            return []

        encodings = ["utf-8", "latin-1", "iso-8859-1"]

        for encoding in encodings:
            try:
                articles = self._read_csv(encoding)
                self.logger.info(f"✅ Got {len(articles)} articles from CSV")
                return articles
            except (UnicodeDecodeError, ParsingException):
                if encoding == encodings[-1]:
                    self.logger.error("❌ CSV reading failed with all encodings")
                    return []
                continue

        return []

    def _read_csv(self, encoding: str) -> List[Article]:
        """Internal method - read CSV with specific encoding"""
        try:
            articles: List[Article] = []

            with open(self.file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    raise ParsingException("CSV file is empty")

                required_fields = {"title", "content", "url"}
                available_fields = set(reader.fieldnames or [])

                if not required_fields.issubset(available_fields):
                    missing = required_fields - available_fields
                    raise ParsingException(f"CSV missing required columns: {missing}")

                for row_num, row in enumerate(reader, start=2):
                    # Skip empty rows
                    if not row or not any((v or "").strip() for v in row.values()):
                        continue

                    title = (row.get("title") or "").strip()
                    content = (row.get("content") or "").strip()
                    url = (row.get("url") or "").strip()

                    # Skip incomplete rows
                    if not title or not content:
                        self.logger.warning(f"Skipping row {row_num}: missing title or content")
                        continue

                    try:
                        article = self._normalize_article(
                            title=title,
                            content=content,
                            source="csv",
                            url=url,
                        )
                        articles.append(article)
                    except Exception as e:
                        self.logger.warning(f"Skipping row {row_num}: {str(e)}")
                        continue

            return articles

        except Exception as e:
            raise ParsingException(f"CSV parsing failed: {str(e)}")
