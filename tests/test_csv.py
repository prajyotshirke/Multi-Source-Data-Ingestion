import pytest
import tempfile
import os
from fetchers.csv_reader import CSVReaderFetcher


class TestCSVReaderFetcher:
    """Test CSV fetcher error handling and file I/O"""
    
    @pytest.fixture
    def fetcher(self):
        """Setup: Create fetcher instance"""
        return CSVReaderFetcher()
    
    @pytest.fixture
    def valid_csv(self):
        """Create valid CSV file"""
        content = '''title,content,url
"Test Article 1","This is test content 1","https://example.com/1"
"Test Article 2","This is test content 2","https://example.com/2"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            return f.name
    
    @pytest.fixture
    def csv_missing_columns(self):
        """CSV with missing required columns"""
        content = '''name,description
"Article","Description"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            return f.name
    
    @pytest.fixture
    def csv_empty_rows(self):
        """CSV with empty rows"""
        content = '''title,content,url
"Article 1","Content 1","url1"


"Article 2","Content 2","url2"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            return f.name
    
    # ============= TEST 1: Valid CSV read =============
    def test_read_valid_csv(self, fetcher, valid_csv):
        """✅ Test: Reads valid CSV correctly"""
        fetcher.file_path = valid_csv
        
        articles = fetcher.fetch()
        
        assert len(articles) == 2
        assert articles[0].title == "Test Article 1"
        assert articles[0].source == "csv"
        assert articles[0].url == "https://example.com/1"

        
        # Cleanup
        os.unlink(valid_csv)
    
    # ============= TEST 2: File not found =============
    def test_file_not_found(self, fetcher):
        """✅ Test: Handles missing file gracefully"""
        fetcher.file_path = "/nonexistent/file.csv"
        
        articles = fetcher.fetch()
        
        # Should return empty list, not crash
        assert articles == []
    
    # ============= TEST 3: Missing required columns =============
    def test_missing_required_columns(self, fetcher, csv_missing_columns):
        """✅ Test: Validates required columns"""
        fetcher.file_path = csv_missing_columns
        
        articles = fetcher.fetch()
        
        # Should fail validation and return empty list
        assert articles == []
        
        os.unlink(csv_missing_columns)
    
    # ============= TEST 4: Empty rows handling =============
    def test_skip_empty_rows(self, fetcher, csv_empty_rows):
        """✅ Test: Skips empty rows gracefully"""
        fetcher.file_path = csv_empty_rows
        
        articles = fetcher.fetch()
        
        # Should skip empty row and return 2 articles
        assert len(articles) == 2
        
        os.unlink(csv_empty_rows)
    
    # ============= TEST 5: Empty title/content =============
    def test_skip_incomplete_rows(self):
        """✅ Test: Skips rows with missing title/content"""
        content = '''title,content,url
"","Missing content","url1"
"Missing content text","","url2"
"Valid","Valid content","url3"
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            csv_file = f.name
        
        fetcher = CSVReaderFetcher(file_path=csv_file)
        articles = fetcher.fetch()
        
        # Only valid row should be returned
        assert len(articles) == 1
        assert articles[0].title == "Valid"

        
        os.unlink(csv_file)
    
    # ============= TEST 6: Output normalization =============
    def test_csv_output_normalization(self, fetcher, valid_csv):
        """✅ Test: CSV output follows schema"""
        fetcher.file_path = valid_csv
        
        articles = fetcher.fetch()
        
        for article in articles:
            assert article.source == "csv"
            assert article.title
            assert article.content
            assert article.url
            assert article.fetched_at
            # URL should be original value (not "N/A" for CSV)
            assert article.url != "N/A"
        
        os.unlink(valid_csv)
    
    # ============= TEST 7: Large CSV =============
    def test_large_csv_handling(self):
        """✅ Test: Handles large CSV without memory issues"""
        content = 'title,content,url\n'
        for i in range(1000):
            content += f'"Article {i}","Content {i}","url{i}"\n'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            csv_file = f.name
        
        fetcher = CSVReaderFetcher(file_path=csv_file)
        articles = fetcher.fetch()
        
        # Should handle 1000 rows
        assert len(articles) == 1000
        
        os.unlink(csv_file)
