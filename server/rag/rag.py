import os
from typing import Any, List, Dict, Optional
import chromadb
from chromadb.config import Settings
import logging
from dataclasses import dataclass
from openai import OpenAI
import json
from dotenv import load_dotenv

from ingestion.models import PaperChunk
from ingestion.processor import OPENAI_API_KEY
from ingestion.section import Section

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

@dataclass
class GeneratedResponse:
    """Response generated from retrieved contexts"""
    answer: str
    citations: List[Dict]
    confidence: float
    sections_referenced: List[str]

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

    def _batch_encode(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batches"""
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = self.embed_client.embeddings.create(
                model="text-embedding-3-small",
                input=batch
            )
            all_embeddings.extend([e.embedding for e in response.data])
        return all_embeddings

    async def add_paper(self,
                           chunks: List[PaperChunk],
                           sections: List[Section],
                           paper_metadata: Dict):
            """Add paper chunks with sanitized metadata"""
            texts = [chunk.text for chunk in chunks]
            ids = [f"{paper_metadata['id']}_{i}" for i in range(len(chunks))]

            # Create section lookup
            section_lookup = {
                section.get_id(): section for section in sections
            }

            # Prepare metadata for each chunk
            metadata = []
            for chunk in chunks:
                section_id = chunk.metadata.get('section_id')
                section = section_lookup.get(section_id)

                # Prepare section data if available
                section_data = None
                if section:
                    section_data = {
                        'id': section.get_id(),
                        'name': section.name,
                        'title': section.title,
                        'is_subsection': section.is_subsection,
                        'parent_name': section.parent_name
                    }

                # Build metadata dict with sanitized values
                meta = prepare_metadata({
                    'paper_id': paper_metadata['id'],
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
            logger.info(f"Added {len(chunks)} chunks from paper {paper_metadata['id']}")

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
            if meta['section_data']:
                section_data = json.loads(meta['section_data'])
                if section_data:  # Check if not empty string
                    section = Section(**section_data)

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
                    'contexts': []
                }
            paper_contexts[paper_id]['contexts'].append(ctx)

        # Format each paper's content
        for paper_id, data in paper_contexts.items():
            meta = data['metadata']
            prompt += f"\n\nPaper [{paper_id}]: {meta['title']}"
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
                prompt += f"\n{ctx.chunk.text}\n"

        prompt += """\nProvide a detailed answer that:
1. Synthesizes information across sources with proper citations [paper_id]
2. Takes advantage of the hierarchical paper structure
3. Notes when information comes from key sections (e.g. methodology, results)
4. Distinguishes between main section and subsection findings
5. Indicates if important equations or figures were referenced
6. Acknowledges any gaps or limitations in the available information"""

        return prompt

    async def generate(self, query: str) -> GeneratedResponse:
        """Generate response with section-aware citations"""
        contexts = await self.retrieve(query)
        prompt = self._build_prompt(query, contexts)

        response = self.embed_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "You are a research assistant specializing in academic papers."
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0.3
        )

        # Track citations and sections
        citations = []
        sections_referenced = []
        for ctx in contexts:
            if f"[{ctx.paper_metadata['id']}]" in response.choices[0].message.content:
                citations.append({
                    "paper_id": ctx.paper_metadata['id'],
                    "title": ctx.paper_metadata['title'],
                    "authors": ctx.paper_metadata['authors'],
                    "published": ctx.paper_metadata['published']
                })
                if ctx.section:
                    sections_referenced.append(ctx.section.get_id())

        return GeneratedResponse(
            answer=response.choices[0].message.content,
            citations=citations,
            confidence=sum(ctx.score for ctx in contexts) / len(contexts),
            sections_referenced=list(set(sections_referenced))
        )
