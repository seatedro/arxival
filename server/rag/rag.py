import os
import re
from typing import Any, List, Dict, Optional, Set
import chromadb
from chromadb.config import Settings
import logging
from dataclasses import dataclass
from openai import OpenAI
import json
from dotenv import load_dotenv

from ingestion.models import ExtractedImage, PaperChunk
from ingestion.processor import OPENAI_API_KEY
from ingestion.section import Section
from ingestion.store import R2ImageStore
from rag.models import StructuredResponse

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEI_SERVER = os.getenv("TEI_SERVER") or "http://localhost:8000"
TEI_TOKEN = os.getenv("TEI_TOKEN") or "dummy_token"
CHROMADB_TOKEN = os.getenv("CHROMADB_TOKEN") or "dummy"
CHROMADB_SERVER = os.getenv("CHROMADB_SERVER") or "http://localhost:8080"

def sanitize_metadata(value: Any) -> Any:
    """Convert metadata values to chroma-compatible primitives"""
    if value is None:
        return ""  # Convert None to empty string
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (list, dict)):
        return json.dumps(value)  # Convert complex types to JSON strings
    else:
        return str(value)  # Convert anything else to string

def prepare_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize all metadata values"""
    return {
        k: sanitize_metadata(v) for k, v in data.items()
    }

@dataclass
class RetrievedContext:
    """Represents a retrieved chunk with its full context"""
    chunk: PaperChunk
    paper_metadata: Dict
    score: float
    section: Optional[Section] = None

    @property
    def relevant_images(self) -> List[Dict]:
            """Get images from this chunk's section"""
            images = self.paper_metadata.get('images', [])
            if not self.section:
                return []

            return [
                img for img in images
                if img['section_id'] == self.section.get_id()
            ]

@dataclass
class GeneratedResponse:
    """Response generated from retrieved contexts"""
    answer: str
    citations: List[Dict]
    confidence: float
    sections_referenced: List[str]
    referenced_images: List[str]

class RAGPipeline:
    def __init__(self,
                 collection_name: str = "papers",
                 batch_size: int = 32):

        # Initialize Chroma client with auth
        self.chroma_client = chromadb.HttpClient(
            host=CHROMADB_SERVER,
            settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                    chroma_client_auth_credentials=CHROMADB_TOKEN
            )
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Setup embedding client
        self.embed_client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        self.batch_size = batch_size

        self.image_store = R2ImageStore("arxival")

    def _batch_encode(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batches"""
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = self.embed_client.embeddings.create(
                model="text-embedding-3-large",
                input=batch
            )
            all_embeddings.extend([e.embedding for e in response.data])
        return all_embeddings

    async def add_paper(self,
                           chunks: List[PaperChunk],
                           sections: List[Section],
                           images: List[ExtractedImage],
                           paper_metadata: Dict):
            """Add paper chunks with sanitized metadata"""
            texts = [chunk.text for chunk in chunks]
            ids = [f"{paper_metadata['id']}_{i}" for i in range(len(chunks))]

            section_lookup = {
                section.get_id(): section for section in sections
            }

            image_metadata = []
            for img in images:
                path = await self.image_store.store_image(paper_metadata["id"], img)
                image_metadata.append({
                    "figure_number": img.figure_number,
                    "paper_id": paper_metadata["id"],
                    "paper_url": paper_metadata["paper_url"],
                    "xref": img.xref,
                    "width": img.width,
                    "height": img.height,
                    "section_id": img.section_id,
                    "storage_path": path
                })

            paper_metadata["images"] = image_metadata


            metadata = []
            for chunk in chunks:
                section_id = chunk.metadata.get('section_id')
                section = section_lookup.get(section_id)

                # Prepare section data if available
                section_data = None
                if section:
                    section_data = {
                        'id': section.get_id(),
                        'start_page': section.start_page,
                        'name': section.name,
                        'title': section.title,
                        'is_subsection': section.is_subsection,
                        'parent_name': section.parent_name
                    }

                # Build metadata dict with sanitized values
                meta = prepare_metadata({
                    'paper_id': paper_metadata['id'],
                    "paper_url": paper_metadata["paper_url"],
                    'chunk_metadata': chunk.metadata,
                    'paper_metadata': paper_metadata,
                    'section_data': section_data
                })

                metadata.append(meta)

            # Get embeddings
            embeddings = self._batch_encode(texts)

            # Add to Chroma
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                ids=ids,
                metadatas=metadata
            )

    async def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedContext]:
        """Retrieve and reconstruct contexts"""
        query_embedding = self._batch_encode([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        contexts = []
        for text, meta, score in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            # Parse JSON-encoded metadata
            chunk_meta = json.loads(meta['chunk_metadata'])
            paper_meta = json.loads(meta['paper_metadata'])

            # Reconstruct chunk
            chunk = PaperChunk(text=text, metadata=chunk_meta)

            # Parse and reconstruct section if available
            section = None
            section_data = meta.get('section_data')
            if section_data:
                try:
                    section_data = json.loads(section_data)
                    if section_data:
                        # Ensure all required fields are present
                        if all(field in section_data for field in ['name', 'title', 'start_page', 'is_subsection']):
                            section = Section(**section_data)
                        else:
                            logger.warning(f"Incomplete section data: {section_data}")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Error parsing section data: {e}")

            contexts.append(RetrievedContext(
                chunk=chunk,
                paper_metadata=paper_meta,
                section=section,
                score=1.0 - score
            ))

        return contexts

    def _build_prompt(self, query: str, contexts: List[RetrievedContext]) -> str:
        """Build structured prompt"""
        prompt = f"""Answer this research question: {query}

Retrieved content from academic papers:"""

        # Group by paper
        paper_contexts = {}
        for ctx in contexts:
            paper_id = ctx.paper_metadata['id']
            if paper_id not in paper_contexts:
                paper_contexts[paper_id] = {
                    'metadata': ctx.paper_metadata,
                    'contexts': [],
                    'images_by_section': {}
                }
            paper_contexts[paper_id]['contexts'].append(ctx)
            relevant_images = ctx.relevant_images
            section_id = ctx.section.get_id() if ctx.section else None
            if relevant_images:
                paper_contexts[paper_id]['images_by_section'][section_id] = relevant_images

        # Format each paper's content
        for paper_id, data in paper_contexts.items():
            meta = data['metadata']
            prompt += f"\n\nPaper [{paper_id}]: {meta['title']}"
            if meta.get('paper_url'):
                prompt += f"\nSource: {meta['paper_url']}"
            prompt += f"\nAuthors: {', '.join(meta['authors'])}"
            prompt += f"\nPublished: {meta['published']}"
            prompt += f"\nCategories: {', '.join(meta['categories'])}"
            prompt += f"\nAbstract: {meta['abstract']}\n"

            # Add chunks with section context
            for ctx in sorted(
                data['contexts'],
                key=lambda x: (
                    x.section.name if x.section else '999',
                    x.chunk.metadata.get('chunk_index', 0)
                )
            ):
                prompt += "\n"
                if ctx.section:
                    prompt += f"From section {ctx.section.name}: {ctx.section.title}"
                    if ctx.section.is_subsection:
                        prompt += f" (subsection of {ctx.section.parent_name})"
                    images = data['images_by_section'].get(ctx.section.get_id(), [])
                    if images:
                        prompt += "\nRelevant figures in this section:"
                        for img in images:
                            prompt += f"\n- Figure {img['xref']}: {img['width']}x{img['height']} image"
                prompt += f"\n{ctx.chunk.text}\n"

        prompt += """\nProvide a detailed answer that:
1. Synthesizes information across sources with proper citations [paper_id]
2. Takes advantage of the hierarchical paper structure
3. References specific figures when they support your points (use figure numbers) (e.g., 'Figure 1 shows...' or 'as seen in Figure 2')
4. Refers to figures in order (Figure 1 before Figure 2, etc.) when discussing each paper
5. Notes when information comes from key sections (e.g. methodology, results)
6. Distinguishes between main section and subsection findings
7. Indicates if important equations or figures were referenced
8. Acknowledges any gaps or limitations in the available information"""

        return prompt

    def _extract_figure_references(self, text: str) -> Set[int]:
            """Extract all figure numbers referenced in text"""
            # Match various ways figures might be referenced
            patterns = [
                r'figure\s+(\d+)',
                r'fig\.\s*(\d+)',
                r'fig\s+(\d+)',
                r'figure\s*(\d+)',
                r'figures\s*(\d+)',
            ]

            figure_numbers = set()
            for pattern in patterns:
                matches = re.finditer(pattern, text.lower())
                figure_numbers.update(int(m.group(1)) for m in matches)

            return figure_numbers

    def _map_figure_number_to_image(self, figure_num: int, section_images: List[Dict]) -> Optional[Dict]:
        """Map a referenced figure number to the actual image metadata"""
        # Sort images by xref to approximate figure ordering
        sorted_images = sorted(section_images, key=lambda x: x['xref'])

        # Try to find the corresponding image
        # Note: This is a simplification - in reality, we might need better mapping
        if 0 <= figure_num - 1 < len(sorted_images):
            return sorted_images[figure_num - 1]
        return None

    async def generate(self, query: str) -> StructuredResponse:
        """Generate structured response with section-aware citations"""
        contexts = await self.retrieve(query)
        prompt = self._build_prompt(query, contexts)
        prompt = self._build_prompt(query, contexts)


        # Request structured output using GPT's parse mode
        response = self.embed_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """You are a research assistant analyzing academic papers.
                Synthesize the information into a structured response with:
                - Introduction section summarizing key points
                - Analysis section diving into details
                - Conclusion section tying everything together
                For each section, include:
                - List the section_ids you cited (e.g. "3.1: Methods")
                - List any figures referenced as paper_id/figure_number
                """
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format=StructuredResponse
        )

        structured_response = response.choices[0].message.parsed

        # Validate and return
        return structured_response
