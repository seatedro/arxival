import pytest
from ingestion.fetcher import PaperFetcher

@pytest.mark.asyncio
async def test_fetch_papers_metadata(paper_fetcher, sample_paper_ids):
    """Test metadata fetching."""
    papers = await paper_fetcher.fetch_papers(paper_ids=sample_paper_ids[:1])
    assert len(papers) > 0

    paper = papers[0]
    required_fields = ['id', 'title', 'abstract', 'authors']
    for field in required_fields:
        assert field in paper
        assert paper[field]

@pytest.mark.asyncio
async def test_fetch_and_process(paper_fetcher):
    """Test PDF download and LlamaParse processing."""
    result = await paper_fetcher.fetch_and_process("2005.14165")

    assert "content" in result
    assert "pdf_path" in result
    assert len(result["content"]) > 0
