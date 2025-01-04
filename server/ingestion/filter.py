from typing import Set, List
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)

class ProcessedPaperTracker:
    """Tracks which papers have already been processed using ChromaDB metadata"""

    def __init__(self, chromadb_host: str, chromadb_token: str, collection_name: str = "papers"):
        self.client = chromadb.HttpClient(
            host=chromadb_host,
            settings=Settings(
                chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                chroma_client_auth_credentials=chromadb_token
            )
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def get_processed_papers(self) -> Set[str]:
        """Get set of all paper IDs that have been processed"""
        try:
            # Query collection metadata to get unique paper_ids
            results = self.collection.get(
                include=['metadatas'],
                where={"paper_id": {"$exists": True}}  # only get entries with paper_id
            )

            # Extract unique paper IDs from metadata
            paper_ids = set()
            for metadata in results['metadatas']:
                if metadata and 'paper_id' in metadata:
                    paper_ids.add(metadata['paper_id'])

            return paper_ids

        except Exception as e:
            logger.error(f"Error getting processed papers: {str(e)}")
            return set()

    def filter_new_papers(self, papers: List[dict]) -> List[dict]:
        """Filter out papers that have already been processed"""
        processed_ids = self.get_processed_papers()
        return [p for p in papers if p['id'] not in processed_ids]
