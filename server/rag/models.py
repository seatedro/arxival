from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class SectionType(str, Enum):
    introduction = "introduction"
    analysis = "analysis"
    conclusion = "conclusion"

class Citation(BaseModel):
    paper_id: str
    section_id: str
    title: str
    authors: List[str]
    paper_url: str
    confidence: float
    quoted_text: Optional[str] = None

class Figure(BaseModel):
    paper_id: str
    paper_url: str
    figure_number: str
    storage_path: str
    width: int
    height: int
    section_id: str

class ResponseMetadata(BaseModel):
    papers_cited: int
    figures_used: int
    overall_confidence: float

class ResponseSection(BaseModel):
    type: SectionType
    content: str
    citations: List[Citation]
    figures: List[Figure]

class StructuredResponse(BaseModel):
    sections: List[ResponseSection]
    metadata: ResponseMetadata
