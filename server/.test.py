import asyncio
import os

from chromadb import HttpClient
from chromadb.config import Settings
from ingestion.fetcher import PaperFetcher
from ingestion.processor import PDFProcessor
from rag.rag import RAGPipeline
from dotenv import load_dotenv

load_dotenv()

CHROMADB_TOKEN = os.getenv("CHROMADB_TOKEN") or "dummy"
CHROMADB_SERVER = os.getenv("CHROMADB_SERVER") or "http://localhost:8080"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "dummy_token"

async def process_paper():
    # Test connection to ChromaDB
    try:
        client = HttpClient(
            host=CHROMADB_SERVER,
            settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                    chroma_client_auth_credentials=CHROMADB_TOKEN
            )
        )
        client.heartbeat()
    except Exception as e:
        print("Could not connect to ChromaDB:", str(e))
        exit(1)
    # 1. fetch paper
    fetcher = PaperFetcher()  # Assuming we need to instantiate these
    paper_data = await fetcher.fetch_papers(paper_ids=["1706.03762"])
    content = await fetcher.fetch_paper_content("1706.03762")

    # 2. process into chunks with sections
    processor = PDFProcessor()
    chunks, sections, images = await processor.process_pdf(content["content"])

    # 3. add to rag pipeline
    rag = RAGPipeline()
    await rag.add_paper(chunks, sections, images, paper_data[0])

    # 4. query!
    response = await rag.generate("Explain the underlying principles of the Transformer architecture.")
    print(f"Answer: {response.answer}")
    print(f"Figures referenced: {response.referenced_images}")
    print(f"Citations: {response.citations}")

# Call the async function
asyncio.run(process_paper())
