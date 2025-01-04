import pytest
import os
from datetime import datetime
from ingestion.fetcher import PaperFetcher
from ingestion.semantic_scholar_fetcher import SemanticScholarFetcher

@pytest.fixture
def paper_fetcher():
    return PaperFetcher()

@pytest.fixture
def sample_paper_ids():
    # known good paper ids for testing
    return ["2005.14165", "2003.00573"]

@pytest.mark.asyncio
async def test_fetch_papers_by_query(paper_fetcher):
    papers = await paper_fetcher.fetch_papers(query="transformers", max_results=2)

    assert len(papers) == 2
    for paper in papers:
        _validate_paper_metadata(paper)

@pytest.mark.asyncio
async def test_fetch_papers_by_ids(paper_fetcher, sample_paper_ids):
    papers = await paper_fetcher.fetch_papers(paper_ids=sample_paper_ids)

    assert len(papers) == len(sample_paper_ids)
    assert papers[0]["id"].split("v")[0] == sample_paper_ids[0]
    _validate_paper_metadata(papers[0])

@pytest.mark.asyncio
async def test_fetch_paper_content(paper_fetcher, sample_paper_ids):
    result = await paper_fetcher.fetch_paper_content(sample_paper_ids[0])

    assert "content" in result
    assert "source_type" in result
    assert result["source_type"] == "pdf"
    assert os.path.exists(result["content"])

@pytest.mark.asyncio
async def test_download_paper_pdf(paper_fetcher, sample_paper_ids):
    pdf_path = await paper_fetcher.download_paper_pdf(sample_paper_ids[0])

    assert os.path.exists(pdf_path)
    assert pdf_path.endswith(".pdf")

def _validate_paper_metadata(paper):
    required = ["id", "title", "abstract", "authors", "categories",
                "published", "updated", "pdf_url"]
    for field in required:
        assert field in paper
        assert paper[field]

    # validate date formats
    datetime.fromisoformat(paper["published"])
    datetime.fromisoformat(paper["updated"])

@pytest.fixture(autouse=True)
async def cleanup():
    yield
    # cleanup downloaded pdfs after tests
    if os.path.exists("./papers"):
        for f in os.listdir("./papers"):
            os.remove(os.path.join("./papers", f))
        os.rmdir("./papers")

@pytest.fixture
def ss_fetcher():
    return SemanticScholarFetcher(min_citations=50)  # lower for testing

@pytest.mark.asyncio
async def test_semantic_fetch_papers_by_query(ss_fetcher):
    papers = await ss_fetcher.fetch_papers(query="transformers", max_results=2)

    assert len(papers) == 2
    for paper in papers:
        _validate_semantic_paper_metadata(paper)
        assert paper["citation_count"] >= ss_fetcher.min_citations

@pytest.mark.asyncio
async def test_semantic_paper_content(ss_fetcher):
    # first fetch papers to populate cache
    papers = await ss_fetcher.fetch_papers(max_results=1)
    paper_id = papers[0]["id"]

    result = await ss_fetcher.fetch_paper_content(paper_id)
    assert "content" in result
    assert "source_type" in result
    assert result["source_type"] == "pdf"
    assert os.path.exists(result["content"])

@pytest.mark.asyncio
async def test_semantic_download_pdf(ss_fetcher):
    # first fetch paper to get valid pdf url
    papers = await ss_fetcher.fetch_papers(max_results=1)
    paper = papers[0]

    pdf_path = await ss_fetcher.download_paper_pdf(
        paper["id"],
        paper["pdf_url"]
    )

    assert os.path.exists(pdf_path)
    assert pdf_path.endswith(".pdf")

@pytest.mark.asyncio
async def test_semantic_rate_limiting(ss_fetcher):
    # test multiple fetches respect rate limiting
    papers1 = await ss_fetcher.fetch_papers(max_results=2)
    papers2 = await ss_fetcher.fetch_papers(max_results=2)

    assert len(papers1) == 2
    assert len(papers2) == 2

@pytest.mark.asyncio
async def test_invalid_paper_id(ss_fetcher):
    with pytest.raises(ValueError):
        await ss_fetcher.fetch_paper_content("invalid_id")

def _validate_semantic_paper_metadata(paper):
    required = ["id", "title", "abstract", "authors", "categories",
                "published", "updated", "pdf_url", "citation_count", "venue"]
    for field in required:
        assert field in paper
        assert paper[field] is not None

    # validate citation count
    assert isinstance(paper["citation_count"], int)
    assert paper["citation_count"] > 0

    # validate dates (might be YYYY-01-01 format)
    datetime.fromisoformat(paper["published"])
    datetime.fromisoformat(paper["updated"])
