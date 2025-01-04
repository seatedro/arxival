from typing import List, Optional
import logging

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
    """Extracts hierarchical section information from markdown academic papers"""

    def __init__(self):
        # Map header depth to section numbering
        self.current_sections = {
            1: 0,  # Main sections: 1, 2, 3
            2: 0,  # Subsections: 1.1, 1.2
            3: 0,  # Sub-subsections: 1.1.1, 1.1.2
        }
        self.last_section = {
            1: None,
            2: None,
            3: None
        }

    async def extract_sections(self, md_text: str) -> List[Section]:
        """Extract sections from markdown text"""
        try:
            sections = []
            current_page = 1

            # Split into lines and process each line
            lines = md_text.split('\n')
            for line in lines:
                # Check for page markers
                if 'Page ' in line:
                    try:
                        current_page = int(line.split('Page ')[-1].split()[0])
                        continue
                    except:
                        pass

                # Process headers
                if line.startswith('#'):
                    # Get header level
                    level = len(line) - len(line.lstrip('#'))
                    if level > 3:  # We only care about h1-h3
                        continue

                    # Clean up header text
                    title = line.lstrip('#').strip()

                    # Generate section number
                    self.current_sections[level] += 1
                    if level == 1:
                        # Reset subsection counters
                        self.current_sections[2] = 0
                        self.current_sections[3] = 0
                        section_num = str(self.current_sections[1])
                    elif level == 2:
                        # Reset sub-subsection counter
                        self.current_sections[3] = 0
                        section_num = f"{self.current_sections[1]}.{self.current_sections[2]}"
                    else:
                        section_num = f"{self.current_sections[1]}.{self.current_sections[2]}.{self.current_sections[3]}"

                    # Create section
                    self.last_section[level] = section_num
                    parent_name = self.last_section[level-1] if level > 2 else None

                    section = Section(
                        name=section_num,
                        title=title,
                        start_page=current_page,
                        is_subsection=level > 2,
                        parent_name=parent_name
                    )
                    sections.append(section)

            return sections

        except Exception as e:
            logger.error(f"Error extracting sections: {str(e)}")
            raise

    def _validate_sections(self, sections: List[Section]) -> List[Section]:
        """Validate extracted sections"""
        valid_sections = []
        seen_numbers = set()

        for section in sorted(sections, key=lambda x: [int(n) for n in x.name.split('.')]):
            # Skip duplicates
            if section.name in seen_numbers:
                continue

            # Skip invalid page numbers
            if section.start_page <= 0:
                continue

            valid_sections.append(section)
            seen_numbers.add(section.name)

        return valid_sections
