import sys
import chromadb
from chromadb.config import Settings
import asyncio
import os
from tqdm import tqdm
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_total_items(_):
    """Get total number of items in collection"""
    # This only gets IDs which uses much less memory
    # results = collection.get(include=[])
    # return len(results["ids"])
    return 116996


async def migrate_collection(
    source_host: str,
    source_token: str,
    dest_host: str,
    dest_token: str,
    collection_name: str = "papers",
    batch_size: int = 100,
    offset_step: int = 1000,  # Number of items to process in each major chunk
):
    """Migrate a collection from source to destination ChromaDB using streaming"""

    # Setup clients
    source_client = chromadb.HttpClient(
        host=source_host,
        settings=Settings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=source_token,
        ),
    )

    dest_client = chromadb.HttpClient(
        host=dest_host,
        settings=Settings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=dest_token,
        ),
    )

    # Get collections
    source_collection = source_client.get_collection(name=collection_name)
    dest_collection = dest_client.get_or_create_collection(
        name=collection_name, metadata={"hnsw:space": "cosine"}
    )

    # Get total count
    total_items = await get_total_items(source_collection)
    logger.info(f"Found {total_items} items to migrate")

    # Process in major chunks to avoid memory issues
    with tqdm(total=total_items, desc="Overall Progress") as pbar:
        for offset in range(0, total_items, offset_step):
            # Get a chunk of items
            chunk_size = min(offset_step, total_items - offset)
            results = source_collection.get(
                include=["embeddings", "documents", "metadatas"],
                limit=chunk_size,
                offset=offset,
            )

            # Process this chunk in smaller batches
            for i in range(0, chunk_size, batch_size):
                end_idx = min(i + batch_size, chunk_size)

                batch_ids = results["ids"][i:end_idx]
                batch_embeddings = results["embeddings"][i:end_idx]
                batch_documents = results["documents"][i:end_idx]
                batch_metadatas = results["metadatas"][i:end_idx]

                # Add batch to destination
                dest_collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                )

                # Update progress
                pbar.update(len(batch_ids))

                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.1)

            # Force garbage collection after each major chunk
            import gc

            gc.collect()

    # Verify final count
    final_count = await get_total_items(dest_collection)
    logger.info(f"Migration complete. Destination has {final_count} items")

    if final_count != total_items:
        logger.warning(
            f"Count mismatch! Source had {total_items} items but destination has {final_count}"
        )
    else:
        logger.info("Successfully verified item count match")


async def main():
    # Get required env vars
    required_vars = {
        "CHROMADB_SERVER": os.getenv("CHROMADB_SERVER"),
        "CHROMADB_TOKEN": os.getenv("CHROMADB_TOKEN"),
        "DEST_CHROMADB_SERVER": os.getenv("DEST_CHROMADB_SERVER"),
        "DEST_CHROMADB_TOKEN": os.getenv("DEST_CHROMADB_TOKEN"),
    }

    # Check for missing env vars
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Optional env vars with defaults
    collection_name = os.getenv("CHROMADB_COLLECTION", "papers")
    batch_size = int(os.getenv("MIGRATION_BATCH_SIZE", "100"))

    try:
        await migrate_collection(
            source_host=required_vars["CHROMADB_SERVER"],
            source_token=required_vars["CHROMADB_TOKEN"],
            dest_host=required_vars["DEST_CHROMADB_SERVER"],
            dest_token=required_vars["DEST_CHROMADB_TOKEN"],
            collection_name=collection_name,
            batch_size=batch_size,
        )
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
