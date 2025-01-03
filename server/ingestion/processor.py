import os
import re
import logging
import pymupdf4llm
from typing import List, Optional
from ingestion.models import PaperChunk
from ingestion.section import Section, SectionExtractor
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "dummy_token"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "dummy_token"

class PDFProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.llm_client = OpenAI(api_key=OPENAI_API_KEY)
        self.section_extractor = SectionExtractor(self.llm_client)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def process_pdf(self, pdf_path: str) -> tuple[List[PaperChunk], List[Section]]:
        """Process PDF and return both chunks and section information"""
        # Get raw text using your existing method
        text = await self._get_pdf_text(pdf_path)

        # Extract sections first
        sections = await self.section_extractor.extract_sections(text)

        # Create chunks with enriched metadata
        chunks = await self._create_chunks(text)

        # Annotate chunks with section information
        self._annotate_chunks_with_sections(chunks, sections)

        return chunks, sections

    def _annotate_chunks_with_sections(self, chunks: List[PaperChunk], sections: List[Section]):
        """Add section metadata to each chunk"""
        for chunk in chunks:
            containing_section = self._find_containing_section(chunk, sections)
            if containing_section:
                chunk.metadata.update({
                    'section_id': containing_section.get_id(),
                    'is_subsection': containing_section.is_subsection
                })

    async def _get_pdf_text(self, pdf_path: str) -> str:
            """Extract clean text from PDF while preserving structure"""
            try:
                # Using your existing pymupdf4llm integration
                md_text = pymupdf4llm.to_markdown(pdf_path)
                return self._clean_text(md_text)
            except Exception as e:
                logger.error(f"Error extracting PDF text: {str(e)}")
                raise

    def _find_containing_section(self, chunk: PaperChunk, sections: List[Section]) -> Optional[Section]:
        """Find which section a chunk belongs to based on page numbers"""
        chunk_page = chunk.metadata.get('page_num')
        if not chunk_page:
            return None

        # Sort sections by page number
        sorted_sections = sorted(sections, key=lambda s: s.start_page)

        # Find the last section that starts before or on this page
        containing_section = None
        for section in sorted_sections:
            if section.start_page <= chunk_page:
                containing_section = section
            else:
                break

        return containing_section

    async def _create_chunks(self, text: str) -> List[PaperChunk]:
        """Create overlapping chunks from document text"""
        chunks = []

        # Split into paragraphs first
        paragraphs = text.split('\n\n')

        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if adding this paragraph would exceed chunk size
            if current_length + len(para) > self.chunk_size and current_chunk:
                # Create chunk from current buffer
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(PaperChunk(
                    text=chunk_text,
                    metadata={
                        'has_equations': bool(re.search(r'\$\$.+?\$\$', chunk_text)),
                        'page_num': self._estimate_page_num(chunk_text)
                    }
                ))

                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    current_chunk = current_chunk[-1:]
                    current_length = len(current_chunk[-1])
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(para)
            current_length += len(para)

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(PaperChunk(
                text=chunk_text,
                metadata={
                    'has_equations': bool(re.search(r'\$\$.+?\$\$', chunk_text)),
                    'page_num': self._estimate_page_num(chunk_text)
                }
            ))

        return chunks

    def _estimate_page_num(self, text: str) -> int:
        """
        Estimate page number for a chunk of text.
        This is a simplified version - you may want to use more sophisticated
        page detection from your existing code.
        """
        # Look for page number indicators in text
        page_matches = re.findall(r'Page (\d+)', text)
        if page_matches:
            return int(page_matches[0])

        # Fallback to position-based estimate
        # You'll want to replace this with your actual page detection logic
        return 1

    def _clean_text(self, text: str) -> str:
        """Clean text while preserving markdown elements"""
        # Remove extra whitespace but preserve markdown
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Preserve equations
        text = re.sub(r'\$\$(.*?)\$\$', r'$$\1$$', text, flags=re.DOTALL)

        # Clean up markdown headers
        text = re.sub(r'^#{1,6}\s*', '# ', text, flags=re.MULTILINE)

        return text.strip()
