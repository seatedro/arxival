import pytest
from ingestion.fetcher import PaperFetcher
from ingestion.processor import PDFProcessor
import os

@pytest.fixture
def paper_fetcher():
    """Provides a PaperFetcher instance."""
    test_dir = "./test_papers"
    os.makedirs(test_dir, exist_ok=True)
    return PaperFetcher()

@pytest.fixture
def paper_processor():
    """Provides a PDFProcessor instance."""
    return PDFProcessor()

@pytest.fixture
def sample_paper_ids():
    """Test paper IDs."""
    return [
        "2005.14165",  # GPT-3 paper
        "1706.03762",  # Transformer paper
    ]
