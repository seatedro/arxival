#!/usr/bin/env python3
import asyncio
import os
import sys
import argparse
from datetime import datetime, timedelta
import logging
from pathlib import Path

from dotenv import load_dotenv

from ingestion.filter import ProcessedPaperTracker

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

CHROMADB_TOKEN = os.getenv("CHROMADB_TOKEN") or "dummy"
CHROMADB_SERVER = os.getenv("CHROMADB_SERVER") or "http://localhost:8080"

from batch import BatchIngester
from ingestion.semantic_scholar_fetcher import SemanticScholarFetcher

def get_date_range(days_back: int = 7) -> tuple[str, str]:
    """Get date range for query, defaults to last week"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

async def main():
    parser = argparse.ArgumentParser(description='Batch ingest papers from Semantic Scholar')

    # Core parameters
    parser.add_argument('--batch-size', type=int, default=10, help='Papers to process in parallel')
    parser.add_argument('--max-papers', type=int, default=50, help='Maximum papers to fetch')
    parser.add_argument('--min-citations', type=int, default=100, help='Minimum citation count')
    parser.add_argument('--force-reprocess', action='store_true',
                        help='Reprocess papers even if already ingested')

    # Date range
    parser.add_argument('--date-from', type=str, help='Start year YYYY')
    parser.add_argument('--date-to', type=str, help='End year YYYY')

    # Query parameters
    parser.add_argument('--query', type=str, default='machine learning',
                       help='Search query (default: machine learning)')
    parser.add_argument('--field', type=str, default='Computer Science',
                       help='Field of study filter')


    args = parser.parse_args()

    date_from, date_to = 2017, None
    if args.date_from:
        date_from = args.date_from
    if args.date_to:
        date_to = args.date_to

    logger.info(f"Starting paper ingestion from {date_from} to {date_to}")
    logger.info(f"Query: {args.query}")
    logger.info(f"Field: {args.field}")
    logger.info(f"Min citations: {args.min_citations}")
    paper_tracker = ProcessedPaperTracker(
        chromadb_host=CHROMADB_SERVER,
        chromadb_token=CHROMADB_TOKEN
    )

    fetcher = SemanticScholarFetcher(
        min_citations=args.min_citations,
        year_from=date_from,
        year_to=date_to
    )

    ingester = BatchIngester(fetcher=fetcher)

    try:
        papers = await fetcher.fetch_papers(
            query=args.query,
            max_results=args.max_papers
        )

        if not args.force_reprocess:
            papers = paper_tracker.filter_new_papers(papers)
            logger.info(f"Found {len(papers)} new papers to process")

            if not papers:
                logger.info("No new papers to process")
                sys.exit(0)

        processed = await ingester.ingest_papers(
            papers=papers,
            max_papers=args.max_papers,
            batch_size=args.batch_size
        )


        logger.info(f"Successfully ingested {processed} papers")

        # Write success marker for monitoring
        with open(log_dir / "last_successful_run", "w") as f:
            f.write(datetime.now().isoformat())

        sys.exit(0)

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
