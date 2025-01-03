import pytest
import asyncio
from ingestion.fetcher import PaperFetcher
from ingestion.processor import PDFProcessor

@pytest.fixture
def paper_fetcher():
    """Provides a PaperFetcher instance for tests."""
    return PaperFetcher()

@pytest.fixture
def paper_processor():
    """Provides a PaperProcessor instance for tests."""
    return PDFProcessor(chunk_size=500, chunk_overlap=50)  # smaller chunks for testing

@pytest.fixture
def sample_paper_ids():
    """Provides a list of paper IDs for testing different scenarios."""
    return [
        "2005.14165",  # GPT-3 paper (should have HTML)
        "1706.03762",  # Transformer paper (might need PDF)
    ]
