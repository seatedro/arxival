from dataclasses import dataclass, field
from typing import Dict, Optional
import base64

@dataclass
class ExtractedImage:
    """Represents an image extracted from a paper"""
    xref: int
    page_num: int
    width: int
    height: int
    image_data: bytes
    extension: str
    figure_number: int
    section_id: Optional[str] = None

    def to_base64(self) -> str:
        return base64.b64encode(self.image_data).decode()

@dataclass
class PaperChunk:
    """
    Represents a chunk of text from an academic paper with rich metadata.
    This class preserves both the content and contextual information
    needed for accurate retrieval.
    """
    # Core content
    text: str

    # Rich metadata about the chunk and its context
    metadata: Dict = field(default_factory=lambda: {
        'paper_id': None,          # Unique identifier for the source paper
        'page_num': None,          # Page number in the source document
        'section_id': None,        # Full section identifier (e.g. "3.2: Implementation Details")
        'parent_section_id': None, # Parent section (e.g. "3: Methods")
        'chunk_index': None,       # Position of chunk within section
        'has_equations': False,    # Whether chunk contains LaTeX equations
        'source_type': None,       # Either 'pdf' or 'html'
    })

    def __post_init__(self):
        """Validate and set default metadata if not provided"""
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

        # Ensure all expected metadata fields exist
        default_metadata = {
            'paper_id': None,
            'page_num': None,
            'section_id': None,
            'parent_section_id': None,
            'chunk_index': None,
            'has_equations': False,
            'source_type': None
        }

        # Update defaults with provided metadata
        self.metadata = {**default_metadata, **self.metadata}

    def get_section(self) -> Optional[str]:
        """Get the section identifier if it exists"""
        return self.metadata.get('section_id')

    def get_page(self) -> Optional[int]:
        """Get the page number if it exists"""
        return self.metadata.get('page_num')

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'text': self.text,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PaperChunk':
        """Create PaperChunk from dictionary representation"""
        return cls(
            text=data['text'],
            metadata=data['metadata']
        )
