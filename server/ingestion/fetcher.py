from typing import List, Optional, Dict
import arxiv
import logging
import aiohttp
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperFetcher:
    def __init__(self):
        self.client = arxiv.Client(
            page_size=100,  # reasonable batch size
            delay_seconds=3.0,  # be nice to arxiv
            num_retries=3
        )

    async def fetch_papers(self,
                          query: Optional[str] = None,
                          paper_ids: Optional[List[str]] = None,
                          max_results: int = 10) -> List[Dict]:
        """
        Fetch papers from ArXiv based on query or paper IDs.
        Returns list of paper metadata + content dicts.
        """
        try:
            # build search based on what we got
            if paper_ids:
                search = arxiv.Search(id_list=paper_ids)
            else:
                search = arxiv.Search(
                    query=query or "cs.AI",  # default to AI papers if no query
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate
                )

            papers = []
            for result in self.client.results(search):
                paper = {
                    "id": result.entry_id.split("/")[-1],
                    "title": result.title,
                    "abstract": result.summary,
                    "authors": [author.name for author in result.authors],
                    "categories": result.categories,
                    "published": result.published.isoformat(),
                    "updated": result.updated.isoformat(),
                    "pdf_url": result.pdf_url,
                }
                papers.append(paper)

            return papers

        except Exception as e:
            logger.error(f"Error fetching papers: {str(e)}")
            raise

    async def fetch_paper_content(self, paper_id: str) -> dict:
        """
        Try to fetch paper content, i originally tried using arxiv's experimental html but it's taking too long to figure out beautiful soup... PDF it is.
        Returns dict with content and source type.
        """
        try:
            async with aiohttp.ClientSession():
                pdf_path = await self.download_paper_pdf(paper_id)
                return {
                    "content": pdf_path,  # return path to downloaded pdf
                    "source_type": "pdf",
                    "url": f"https://arxiv.org/pdf/{paper_id}.pdf"
                }

        except Exception as e:
            logger.error(f"Error fetching content for paper {paper_id}: {str(e)}")
            raise

    async def download_paper_pdf(self, paper_id: str, output_dir: str = "./papers") -> str:
        """
        Download PDF for a specific paper.
        Returns path to downloaded file.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search))
            filepath = paper.download_pdf(dirpath=output_dir)
            logger.info(f"Downloaded PDF for paper {paper_id} to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error downloading PDF for paper {paper_id}: {str(e)}")
            raise
