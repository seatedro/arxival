import asyncio
import argparse
from datetime import datetime, timedelta
import logging
from rich.logging import RichHandler
from rich.prompt import Prompt, Confirm

from batch import BatchIngester

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> str:
    """Convert date string to arxiv format YYYYMMDD"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%Y%m%d")
    except ValueError:
        return date_str

async def main():
    parser = argparse.ArgumentParser(description='Batch ingest papers from arXiv')

    parser.add_argument('--batch-size', type=int, default=10, help='Papers to process in parallel')
    parser.add_argument('--max-papers', type=int, default=50, help='Maximum papers to fetch')

    parser.add_argument('--category', type=str, help='arXiv category (e.g. cs.AI, cs.CL)')
    parser.add_argument('--date-from', type=str, help='Start date YYYY-MM-DD')
    parser.add_argument('--date-to', type=str, help='End date YYYY-MM-DD')
    parser.add_argument('--query', type=str, help='Custom arXiv query')

    args = parser.parse_args()

    if not args.query and not args.category:
        print("\n🤖 arXival Batch Ingestion CLI")
        print("----------------------------")

        categories = [
            "cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.NE",
            "stat.ML", "cs.IR", "cs.CC", "cs.DC", "cs.PL"
        ]
        category = Prompt.ask(
            "Choose category",
            choices=categories,
            default="cs.AI"
        )

        today = datetime.now()
        one_month_ago = today - timedelta(days=30)

        date_from = Prompt.ask(
            "From date (YYYY-MM-DD)",
            default=one_month_ago.strftime("%Y-%m-%d")
        )
        date_to = Prompt.ask(
            "To date (YYYY-MM-DD)",
            default=today.strftime("%Y-%m-%d")
        )

        max_papers = int(Prompt.ask(
            "Maximum papers to fetch",
            default="50"
        ))

        query = f'cat:{category}'
        if date_from or date_to:
            date_from = parse_date(date_from)
            date_to = parse_date(date_to)
            query += f' AND submittedDate:[{date_from} TO {date_to}]'

    else:
        if args.query:
            query = args.query
        else:
            query = f'cat:{args.category}'
            if args.date_from or args.date_to:
                date_from = parse_date(args.date_from or '20200101')
                date_to = parse_date(args.date_to or datetime.now().strftime("%Y%m%d"))
                query += f' AND submittedDate:[{date_from} TO {date_to}]'
        max_papers = args.max_papers

    print(f"\nQuery: {query}")
    print(f"Max papers: {max_papers}")
    print(f"Batch size: {args.batch_size}")

    if not Confirm.ask("Proceed with ingestion?"):
        return

    ingester = BatchIngester()
    processed = await ingester.ingest_papers(
        query=query,
        max_papers=max_papers,
        batch_size=args.batch_size
    )

    logger.info(f"Completed ingestion of {processed} papers")

    while Confirm.ask("Ingest more papers?"):
        offset = processed
        more_papers = int(Prompt.ask(
            "How many more papers?",
            default="50"
        ))

        processed += await ingester.ingest_papers(
            query=query,
            max_papers=more_papers,
            batch_size=args.batch_size
        )

        logger.info(f"Total papers processed: {processed}")

if __name__ == "__main__":
    asyncio.run(main())
