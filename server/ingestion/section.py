from dataclasses import dataclass
from typing import List, Optional
import logging

from openai import OpenAI
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.shared import ResponseFormatJSONObject
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Section(BaseModel):
    """Represents a section in an academic paper"""
    name: str = Field(..., description="Section number (e.g. '3.2' or '4')")
    title: str = Field(..., description="Section title (e.g. 'Implementation Details')")
    start_page: int = Field(..., description="Page number where section begins")
    is_subsection: bool = Field(..., description="Whether this is a subsection (e.g. 3.2 vs 3)")
    parent_name: Optional[str] = Field(None, description="Name of parent section (e.g. '3' is parent of '3.2')")

    def get_id(self) -> str:
        """Generate unique identifier for this section"""
        return f"{self.name}: {self.title}"

class SectionList(BaseModel):
    """List of sections found in a paper"""
    sections: List[Section] = Field(..., description="All sections found in the paper")


class SectionExtractor:
    """Extracts hierarchical section information from academic papers using LLM"""

    def __init__(self, llm_client: OpenAI):
        self.client = llm_client

    async def extract_sections(self, pdf_text: str) -> List[Section]:
        """Extract sections using OpenAI's structured parsing"""
        try:
            # First pass to get initial sections
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """
                     Extract all section headers from this academic paper text.
                     Only include actual section headers (e.g. "3. Methods"), not figures or tables.
                     For each section, identify its number, title, start page, and whether it's a subsection.
                     """},
                    {"role": "user", "content": pdf_text}
                ],
                response_format=SectionList
            )

            if not completion.choices[0].message.parsed:
                raise ValueError("No completion choices returned")

            sections = completion.choices[0].message.parsed.sections

            # Validate and structure sections
            validated = self._validate_sections(sections)
            structured = self._build_hierarchy(validated)

            logger.info(f"Successfully extracted {len(structured)} sections")
            return structured

        except Exception as e:
            logger.error(f"Error extracting sections: {str(e)}")
            raise

    def _validate_sections(self, sections: List[Section]) -> List[Section]:
        """Validate extracted sections for coherence"""
        valid_sections = []
        seen_numbers = set()

        for section in sorted(sections, key=lambda x: x.name):
            # Skip duplicates
            if section.name in seen_numbers:
                continue

            # Basic validation
            if section.start_page <= 0:
                continue

            # Validate subsection marking
            section.is_subsection = '.' in section.name

            valid_sections.append(section)
            seen_numbers.add(section.name)

        return valid_sections

    def _build_hierarchy(self, sections: List[Section]) -> List[Section]:
        """Build parent-child relationships between sections"""
        for section in sections:
            if section.is_subsection:
                parent_name = section.name.split('.')[0]
                section.parent_name = parent_name

        return sections
