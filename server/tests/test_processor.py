import pytest
from ingestion.section import Section

@pytest.mark.asyncio
async def test_fetch_and_process(paper_fetcher, paper_processor):
    """test full pipeline - fetch pdf and process into chunks w/ sections"""

    # fetch paper pdf
    paper_data = await paper_fetcher.fetch_paper_content("2005.14165")
    assert paper_data["source_type"] == "pdf"

    # process into chunks with sections
    chunks, sections = await paper_processor.process_pdf(paper_data["content"])

    # validate chunks
    assert len(chunks) > 0
    assert all("section_id" in c.metadata for c in chunks)
    assert all("page_num" in c.metadata for c in chunks)

    # validate sections
    assert len(sections) > 0
    assert all(isinstance(s, Section) for s in sections)
    assert any(not s.is_subsection for s in sections) # has top-level sections
    assert any(s.is_subsection for s in sections) # has subsections

@pytest.mark.asyncio
async def test_chunk_section_annotation(paper_processor):
    """test that chunks get properly tagged with section info"""
    sample_text = "1. Methods\nThis section..."

    chunks = await paper_processor._create_chunks(sample_text)
    sections = await paper_processor.section_extractor.extract_sections(sample_text)

    paper_processor._annotate_chunks_with_sections(chunks, sections)

    assert all("section_id" in c.metadata for c in chunks)
