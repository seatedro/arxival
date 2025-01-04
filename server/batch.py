import asyncio
from datetime import datetime
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Set
import aiohttp
import backoff  # for exponential backoff on failures
import rich.traceback
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID

from ingestion.fetcher import PaperFetcher
from ingestion.semantic_scholar_fetcher import SemanticScholarFetcher
from ingestion.processor import PDFProcessor
from rag.rag import RAGPipeline
import traceback

# Setup nice logging with rich
rich.traceback.install()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

class BatchIngester:
    def __init__(self,
                    fetcher: PaperFetcher | SemanticScholarFetcher = PaperFetcher(),
                 output_dir: str = "./papers",
                 cache_dir: str = "./cache",
                 checkpoint_file: str = "ingestion_checkpoint.json",
                 error_log: str = "ingestion_errors.jsonl",
                 skip_log: str = "ingestion_skipped.jsonl"):
        self.fetcher = fetcher
        self.processor = PDFProcessor()
        self.rag = RAGPipeline()

        # Setup directories
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Files for tracking state
        self.checkpoint_file = Path(checkpoint_file)
        self.error_log = Path(error_log)
        self.skip_log = Path(skip_log)

        self.skipped_papers: Set[str] = set()
        if self.skip_log.exists():
            with open(self.skip_log) as f:
                self.skipped_papers = {
                    json.loads(line)["paper_id"]
                    for line in f
                }

        # Cache for paper metadata
        self.metadata_cache: Dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self):
        """Load cached paper metadata"""
        cache_file = self.cache_dir / "metadata_cache.json"
        if cache_file.exists():
            with open(cache_file) as f:
                self.metadata_cache = json.load(f)
                logger.info(f"Loaded {len(self.metadata_cache)} cached paper metadata")

    def _save_cache(self):
        """Save paper metadata cache"""
        cache_file = self.cache_dir / "metadata_cache.json"
        with open(cache_file, "w") as f:
            json.dump(self.metadata_cache, f)

    def _log_error(self, paper_id: str, error: Exception, stage: str):
        """Log error details to error log file"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "paper_id": paper_id,
            "stage": stage,
            "error": str(error),
            "traceback": traceback.format_exc()
        }

        with open(self.error_log, "a") as f:
            f.write(json.dumps(error_entry) + "\n")

    def _log_skip(self, paper_id: str, reason: str):
        """Log skipped paper"""
        skip_entry = {
            "timestamp": datetime.now().isoformat(),
            "paper_id": paper_id,
            "reason": reason
        }

        with open(self.skip_log, "a") as f:
            f.write(json.dumps(skip_entry) + "\n")

        self.skipped_papers.add(paper_id)

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def _fetch_with_retry(self, paper_id: str) -> dict:
        """Fetch paper content with retry logic"""
        try:
            return await self.fetcher.fetch_paper_content(paper_id)
        except Exception as e:
            self._log_error(paper_id, e, "fetch")
            raise

    async def ingest_papers(self,
                          query: Optional[str] = None,
                          papers: Optional[list] = None,
                          max_papers: int = 100,
                          batch_size: int = 10,
                          ):
        """Batch ingest papers with progress tracking and error handling"""

        # Load checkpoint
        processed_ids = set()
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file) as f:
                processed_ids = set(json.load(f))
                logger.info(f"Resuming from checkpoint with {len(processed_ids)} papers")

        # Fetch or load papers
        if not papers:
            papers = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:

                fetch_task = progress.add_task("Fetching papers...", total=None)
                try:
                    papers = await self.fetcher.fetch_papers(
                        query=query,
                        max_results=max_papers,
                    )
                    # Cache metadata
                    for paper in papers:
                        self.metadata_cache[paper["id"]] = paper
                    self._save_cache()

                except Exception as e:
                    logger.error(f"Failed to fetch papers: {str(e)}")
                    return 0
                finally:
                    progress.remove_task(fetch_task)

        # Filter new papers
        papers = [p for p in papers if p["id"] not in processed_ids]
        if not papers:
            logger.info("No new papers to process")
            return len(processed_ids)

        logger.info(f"Processing {len(papers)} new papers in batches of {batch_size}")

        # Process batches with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:

            overall_task = progress.add_task(
                "Overall progress",
                total=len(papers)
            )

            for i in range(0, len(papers), batch_size):
                batch = papers[i:i + batch_size]
                batch_task = progress.add_task(
                    f"Processing batch {i//batch_size + 1}",
                    total=len(batch)
                )

                tasks = []
                for paper in batch:
                    tasks.append(self.process_single_paper(
                        paper,
                        progress,
                        batch_task
                    ))

                # Process batch
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Update checkpoint
                newly_processed = []
                for paper, result in zip(batch, results):
                    if not isinstance(result, Exception):
                        newly_processed.append(paper["id"])
                        progress.advance(overall_task)
                    else:
                        logger.error(f"Failed paper {paper['id']}: {str(result)}")

                processed_ids.update(newly_processed)
                with open(self.checkpoint_file, "w") as f:
                    json.dump(list(processed_ids), f)

                # Cleanup batch progress
                progress.remove_task(batch_task)

                # Rate limit between batches
                if i + batch_size < len(papers):
                    delay_task = progress.add_task(
                        "Cooling down...",
                        total=30
                    )
                    for _ in range(30):
                        await asyncio.sleep(1)
                        progress.advance(delay_task)
                    progress.remove_task(delay_task)

        return len(processed_ids)

    async def process_single_paper(self,
                                 paper_metadata: dict,
                                 progress: Progress,
                                 parent_task: TaskID):
        """Process single paper with granular progress tracking"""
        paper_id = paper_metadata["id"]

        if paper_id in self.skipped_papers:
            progress.advance(parent_task)
            return False

        try:
            # 1. Check cache first
            cached_pdf = self.cache_dir / f"{paper_id}.pdf"
            if not cached_pdf.exists():
                # Fetch and cache
                paper_data = await self._fetch_with_retry(paper_id)
                # Save PDF to cache
                if not paper_data:
                    self._log_skip(paper_id, "fetch_failed")
                    return False
                import shutil
                shutil.copy2(paper_data["content"], cached_pdf)
            else:
                paper_data = {
                    "content": str(cached_pdf),
                    "source_type": "pdf",
                    "url": f"https://arxiv.org/pdf/{paper_id}.pdf"
                }

            progress.advance(parent_task, 0.4)  # 40% progress

            # 2. Process PDF
            try:
                chunks, sections, images = await self.processor.process_pdf(
                    paper_data["content"]
                )
                if not chunks or not sections:
                    self._log_skip(paper_id, "processing_failed")
                    return False
                progress.advance(parent_task, 0.3)  # 70% progress
            except Exception as e:
                self._log_error(paper_id, e, "process")
                self._log_skip(paper_id, "process_error")
                raise

            # 3. Add to RAG
            try:
                await self.rag.add_paper(chunks, sections, images, paper_metadata)
                progress.advance(parent_task, 0.3)  # 100% progress
            except Exception as e:
                self._log_error(paper_id, e, "rag")
                self._log_skip(paper_id, "rag_error")
                raise

            return True

        except Exception as e:
            self._log_error(paper_id, e, "overall")
            self._log_skip(paper_id, "rag_error")
            raise

async def main():
    # Example usage
    ingester = BatchIngester()

    # Get recent AI papers about LLMs
    query = '''cat:cs.AI AND submittedDate:[20240101 TO 20241231]'''

    processed = await ingester.ingest_papers(
        query=query,
        max_papers=50,
        batch_size=5
    )

    logger.info(f"Completed ingestion of {processed} papers")

    # Show error summary if any
    if ingester.error_log.exists():
        with open(ingester.error_log) as f:
            errors = [json.loads(line) for line in f]
            if errors:
                logger.warning(f"Encountered {len(errors)} errors during ingestion")
                for e in errors[:5]:  # Show first 5 errors
                    logger.warning(
                        f"Paper {e['paper_id']} failed in {e['stage']}: {e['error']}"
                    )

if __name__ == "__main__":
    asyncio.run(main())
