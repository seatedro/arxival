from typing import Set, List
from pinecone import Pinecone
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

class ProcessedPaperTracker:
    """Tracks which papers have already been processed using ChromaDB metadata"""

    def __init__(self, chromadb_host: str, chromadb_token: str, collection_name: str = "papers"):
        self.client = Pinecone(
            api_key=os.getenv("PINECONE_API_KEY"),
        )
        self.collection = self.client.Index("papers", host=os.getenv("PINECONE_HOST") or "")

    def get_processed_papers(self) -> Set[str]:
        """Get set of all paper IDs that have been processed"""
        try:
            # Query collection metadata to get unique paper_ids
            results = self.collection.describe_index_stats()

            return results.total_vector_count

        except Exception as e:
            logger.error(f"Error getting processed papers: {str(e)}")
            return set()

    def filter_new_papers(self, papers: List[dict]) -> List[dict]:
        """Filter out papers that have already been processed"""
        processed_ids = self.get_processed_papers()
        return [p for p in papers if p['id'] not in processed_ids]
