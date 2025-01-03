import pytest
from ingestion.fetcher import PaperFetcher
from ingestion.processor import PDFProcessor
import json

@pytest.fixture
def processor():
    return PDFProcessor(chunk_size=500, chunk_overlap=50)

@pytest.fixture
def paper_fetcher():
    return PaperFetcher()

@pytest.fixture
def test_papers():
    """Papers we know should work well for testing."""
    return [
        ("1706.03762", "Attention Is All You Need"),  # Transformer paper
        ("2006.07733", "BYOL")  # Paper with lots of equations
    ]

@pytest.mark.asyncio
async def test_pdf_processing(processor, paper_fetcher, test_papers, tmp_path):
    """Test complete PDF processing pipeline."""
    for paper_id, paper_name in test_papers:
        print(f"\nTesting {paper_name} ({paper_id})")

        try:
            # First get the PDF
            content_data = await paper_fetcher.fetch_paper_content(paper_id)
            assert content_data["content"], "Should get PDF content"

            # Process the PDF
            chunks = processor.process_pdf(content_data["content"], paper_id)
            assert len(chunks) > 0, "Should create chunks"

            # Check for abstract
            abstract_chunks = [c for c in chunks if c.section == "abstract"]
            assert len(abstract_chunks) > 0, "Should have abstract"
            assert len(abstract_chunks[0].text) > 100, "Abstract should be substantial"

            # Check for sections
            sections = {c.section for c in chunks if c.section}
            assert len(sections) > 1, "Should find multiple sections"

            # Save sample output for manual inspection
            output_file = tmp_path / f"{paper_id}_chunks.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "paper_id": paper_id,
                    "total_chunks": len(chunks),
                    "sections_found": list(sections),
                    "sample_chunks": [{
                        "section": c.section,
                        "text_preview": c.text[:200],
                        "metadata": c.metadata
                    } for c in chunks[:3]]
                }, f, indent=2)

            print(f"Saved chunk samples to {output_file}")
            print(f"Found sections: {sections}")
            print(f"Total chunks: {len(chunks)}")

        except Exception as e:
            print(f"Error processing {paper_id}: {e}")
            raise

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
