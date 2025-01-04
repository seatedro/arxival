import pytest
from pathlib import Path
import pymupdf4llm
from ingestion.section import SectionExtractor

TEST_PDF = """your arxiv paper test file will go here in ./test_papers/"""

@pytest.fixture(params=list(Path("./papers").glob("*.pdf")))
def test_pdf_path(request):
    """Test with all PDFs in papers directory"""
    pdf_path = request.param
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found at {pdf_path}")
    return str(pdf_path)

@pytest.mark.asyncio
async def test_pdf_to_markdown_conversion(test_pdf_path):
    """Test conversion of PDF to markdown with section headers"""

    # Convert PDF to markdown
    md_text = pymupdf4llm.to_markdown(test_pdf_path, show_progress=False)
    assert md_text, "Markdown conversion failed"

    # Basic markdown structure checks
    assert "# " in md_text, "No headers found in markdown"
    assert "## " in md_text, "No subheaders found in markdown"

    # Split into lines and check header structure
    lines = md_text.split('\n')
    headers = [line for line in lines if line.startswith('#')]
    assert len(headers) > 0, "No headers found"

    # Print first few headers for inspection
    print("\nFound headers:")
    for h in headers[:5]:
        print(h)

@pytest.mark.asyncio
async def test_section_extraction_from_pdf(test_pdf_path):
    """Test full pipeline - PDF to markdown to sections"""

    # Convert PDF
    md_text = pymupdf4llm.to_markdown(test_pdf_path, show_progress=False)

    # Extract sections
    extractor = SectionExtractor()
    sections = await extractor.extract_sections(md_text)

    assert len(sections) > 0, "No sections extracted"

    # Verify section structure
    main_sections = [s for s in sections if not s.is_subsection]
    sub_sections = [s for s in sections if s.is_subsection]

    assert len(main_sections) > 0, "No main sections found"
    assert len(sub_sections) > 0, "No subsections found"

    # Print section hierarchy for inspection
    print("\nExtracted section hierarchy:")
    for section in sections:
        indent = "  " * (len(section.name.split('.')) - 1)
        print(f"{indent}{section.name}: {section.title} (page {section.start_page})")

    # Verify page numbers
    assert all(s.start_page > 0 for s in sections), "Invalid page numbers found"
    page_order = [s.start_page for s in sections]
    assert page_order == sorted(page_order), "Sections not in page order"
