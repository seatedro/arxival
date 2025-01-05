from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class TimingStats(BaseModel):
    """Track timing for different stages of the RAG pipeline"""

    retrieval_ms: Optional[float] = None
    embedding_ms: Optional[float] = None
    generation_ms: Optional[float] = None
    total_ms: Optional[float] = None


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


class TimedMetadata(ResponseMetadata):
    timing: TimingStats


class ResponseParagraph(BaseModel):
    content: str
    citations: List[Citation]
    figures: List[Figure]


class StructuredResponse(BaseModel):
    paragraphs: List[ResponseParagraph]
    metadata: TimedMetadata
