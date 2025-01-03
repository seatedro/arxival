from dataclasses import dataclass
from typing import List, Optional, Dict
import logging
import re
import pymupdf4llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PaperChunk:
    """A chunk of paper content with its metadata"""
    text: str
    section: Optional[str]
    chunk_id: str
    metadata: Dict = None

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_pdf(self, pdf_path: str, paper_id: str) -> List[PaperChunk]:
        """
        Process a PDF file and return chunks of text with metadata.
        Uses pymupdf4llm to get clean markdown output, which preserves structure better.
        """
        try:
            # Convert PDF to markdown - this preserves structure nicely
            md_text = pymupdf4llm.to_markdown(pdf_path)
            logger.info(f"Successfully converted PDF to markdown for {paper_id}")

            # Split content into sections
            chunks = []
            sections = self._split_into_sections(md_text)

            # Process each section
            for section_title, content in sections.items():
                # Handle abstract specially
                if section_title.lower() == "abstract":
                    chunks.append(PaperChunk(
                        text=self._clean_text(content),
                        section="abstract",
                        chunk_id=f"{paper_id}_abstract",
                        metadata={"type": "abstract"}
                    ))
                else:
                    # Create overlapping chunks for other sections
                    section_chunks = self._create_chunks(
                        content, section_title, paper_id
                    )
                    chunks.extend(section_chunks)

            logger.info(f"Created {len(chunks)} chunks for paper {paper_id}")
            return chunks

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise

    def _split_into_sections(self, md_text: str) -> Dict[str, str]:
        """Split markdown text into sections based on headers."""
        sections = {}
        current_section = "unknown"
        current_content = []

        # Split on markdown headers (# Title, ## Subtitle, etc)
        lines = md_text.split('\n')
        for line in lines:
            # Check if line is a header
            header_match = re.match(r'^#{1,6}\s+(.+)$', line)
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                    current_content = []

                current_section = header_match.group(1).strip()
            else:
                # Add line to current section
                if line.strip():
                    current_content.append(line)

        # Don't forget the last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _create_chunks(self, text: str, section: str, paper_id: str) -> List[PaperChunk]:
        """Create overlapping chunks from text while preserving important elements."""
        chunks = []
        text = self._clean_text(text)

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
                    section=section,
                    chunk_id=f"{paper_id}_{section}_{len(chunks)}",
                    metadata={"has_equations": bool(re.search(r'\$\$.+?\$\$', chunk_text))}
                ))

                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    # Keep the last paragraph for overlap
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
                section=section,
                chunk_id=f"{paper_id}_{section}_{len(chunks)}",
                metadata={"has_equations": bool(re.search(r'\$\$.+?\$\$', chunk_text))}
            ))

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean text while preserving markdown elements."""
        # Remove extra whitespace but preserve markdown
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
