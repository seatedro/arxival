import os
import re
import logging
import pymupdf4llm
import pymupdf
from typing import List, Optional, Tuple
from ingestion.models import ExtractedImage, PaperChunk
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
        self.min_dimension = 100
        self.min_size_bytes = 2048

    async def process_pdf(self, pdf_path: str) -> tuple[List[PaperChunk], List[Section], List[ExtractedImage]]:
        """Process PDF and return both chunks and section information"""
        # Get raw text using your existing method
        text = await self._get_pdf_text(pdf_path)

        # Extract sections first
        sections = await self.section_extractor.extract_sections(text)

        # Create chunks with enriched metadata
        chunks = await self._create_chunks(text)

        # Annotate chunks with section information
        self._annotate_chunks_with_sections(chunks, sections)

        images = await self._extract_images(pdf_path, sections)

        return chunks, sections, images

    async def _extract_images(self, pdf_path: str, sections: List[Section]) -> List[ExtractedImage]:
            """Extract images while preserving section context"""
            doc = pymupdf.open(pdf_path)
            images = []
            seen_xrefs = set()

            for page_num in range(doc.page_count):
                page_images = doc.get_page_images(page_num)

                for img in page_images:
                    xref = img[0]
                    if xref in seen_xrefs:
                        continue

                    width, height = img[2], img[3]
                    if min(width, height) <= self.min_dimension:
                        continue

                    image_dict = self._recover_image(doc, img)
                    if len(image_dict["image"]) <= self.min_size_bytes:
                        continue

                    containing_section = self._find_containing_section(
                        PaperChunk(text="", metadata={"page_num": page_num + 1}),
                        sections
                    )

                    images.append(ExtractedImage(
                        xref=xref,
                        page_num=page_num + 1,
                        width=width,
                        height=height,
                        image_data=image_dict["image"],
                        extension=image_dict["ext"],
                        section_id=containing_section.get_id() if containing_section else None
                    ))
                    seen_xrefs.add(xref)

            return images

    def _recover_image(self, doc: pymupdf.Document, img: Tuple) -> dict:
            """Handle image extraction with mask support"""
            xref, smask = img[0], img[1]

            if smask > 0:
                pix0 = pymupdf.Pixmap(doc.extract_image(xref)["image"])
                if pix0.alpha:
                    pix0 = pymupdf.Pixmap(pix0, 0)
                mask = pymupdf.Pixmap(doc.extract_image(smask)["image"])

                try:
                    pix = pymupdf.Pixmap(pix0, mask)
                except:
                    pix = pymupdf.Pixmap(doc.extract_image(xref)["image"])

                ext = "png" if pix0.n <= 3 else "pam"
                return {
                    "ext": ext,
                    "colorspace": pix.colorspace.n,
                    "image": pix.tobytes(ext)
                }

            if "/ColorSpace" in doc.xref_object(xref, compressed=True):
                pix = pymupdf.Pixmap(doc, xref)
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                return {
                    "ext": "png",
                    "colorspace": 3,
                    "image": pix.tobytes("png")
                }

            return doc.extract_image(xref)

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
