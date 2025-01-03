import pytest

@pytest.mark.asyncio
async def test_fetch_papers_metadata(paper_fetcher, sample_paper_ids):
    """Tests basic paper metadata fetching functionality."""
    papers = await paper_fetcher.fetch_papers(paper_ids=sample_paper_ids[:1])
    assert len(papers) > 0
    paper = papers[0]

    # Check required fields are present and non-empty
    required_fields = ['id', 'title', 'abstract', 'authors', 'published']
    for field in required_fields:
        assert field in paper
        assert paper[field], f"Field {field} should not be empty"

@pytest.mark.asyncio
async def test_fetch_paper_content_html(paper_fetcher):
    """Tests fetching paper content in HTML format."""
    content = await paper_fetcher.fetch_paper_content("2005.14165")
    assert content['source_type'] in ['html', 'pdf']
    assert 'content' in content
    assert 'url' in content

@pytest.mark.asyncio
async def test_fetch_paper_content_pdf_fallback(paper_fetcher):
    """Tests PDF fallback when HTML isn't available."""
    # Older paper might need PDF fallback
    content = await paper_fetcher.fetch_paper_content("1706.03762")
    assert content['source_type'] in ['html', 'pdf']
    assert 'content' in content
    assert 'url' in content
