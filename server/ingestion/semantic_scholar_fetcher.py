from typing import List, Optional, Dict
import logging
import aiohttp
import os
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticScholarFetcher:
    """Fetches papers from Semantic Scholar API with pagination support"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

    def __init__(self, min_citations: int = 100):
        self.min_citations = min_citations
        self.fields = [
            "title", "abstract", "year", "authors", "openAccessPdf",
            "citationCount", "venue", "publicationDate", "fieldsOfStudy"
        ]
        self.paper_cache = {}

    async def fetch_papers(self,
                          query: Optional[str] = "machine learning",
                          max_results: int = 100) -> List[Dict]:
        """
        Fetch papers from Semantic Scholar based on query or paper IDs.
        Returns list of paper metadata + content dicts.
        """
        try:
            params = {
                'query': query or 'machine learning',
                'limit': min(max_results, 1000),
                'fields': ','.join(self.fields),
                'sort': 'citationCount:desc',
                'openAccessPdf': '',
                'year': '2017-2024',
                'fieldsOfStudy': 'Computer Science',
                'minCitationCount': str(self.min_citations)
            }

            papers = []
            next_token = None

            while len(papers) < max_results:
                if next_token:
                    params['token'] = next_token

                async with aiohttp.ClientSession() as session:
                    async with session.get(self.BASE_URL, params=params) as resp:
                        if resp.status != 200:
                            logger.error(f"API error: {resp.status}")
                            break

                        data = await resp.json()

                        # Process results
                        for paper in data['data']:
                            processed = self._process_paper(paper)
                            if processed:
                                papers.append(processed)
                                self.paper_cache[processed['id']] = processed

                        # Check pagination
                        next_token = data.get('token')
                        if not next_token or len(papers) >= max_results:
                            break

                await asyncio.sleep(3)  # Rate limiting

            logger.info(f"Fetched {len(papers)} papers")
            return papers[:max_results]

        except Exception as e:
            logger.error(f"Error fetching papers: {str(e)}")
            raise

    def _process_paper(self, paper: Dict) -> Optional[Dict]:
        """Process raw API response into standard format"""
        try:
            if not paper.get('openAccessPdf'):
                return None

            return {
                "id": paper.get('paperId'),
                "title": paper.get('title'),
                "abstract": paper.get('abstract'),
                "authors": [author['name'] for author in paper.get('authors', [])],
                "categories": paper.get('fieldsOfStudy', []),
                "published": paper.get('publicationDate') or f"{paper.get('year')}-01-01",
                "updated": paper.get('publicationDate') or f"{paper.get('year')}-01-01",
                "pdf_url": paper['openAccessPdf']['url'],
                "citation_count": paper.get('citationCount'),
                "venue": paper.get('venue')
            }
        except Exception as e:
            logger.error(f"Error processing paper: {str(e)}")
            return None

    async def fetch_paper_content(self, paper_id: str) -> dict:
        """Get paper content using cached metadata"""
        try:
            if paper_id not in self.paper_cache:
                raise ValueError(f"Paper {paper_id} not found in cache. Fetch papers first.")

            paper = self.paper_cache[paper_id]
            pdf_path = await self.download_paper_pdf(paper_id, paper['pdf_url'])

            return {
                "content": pdf_path,
                "source_type": "pdf",
                "url": paper['pdf_url']
            }

        except Exception as e:
            logger.error(f"Error fetching content for paper {paper_id}: {str(e)}")
            raise

    async def download_paper_pdf(self,
                               paper_id: str,
                               pdf_url: str,
                               output_dir: str = "./papers") -> str:
        """
        Download PDF from provided URL.
        Returns path to downloaded file.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f"{paper_id}.pdf")

            if os.path.exists(filepath):
                logger.info(f"Paper {paper_id} already downloaded")
                return filepath

            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Failed to download PDF: {resp.status}")

                    with open(filepath, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

            logger.info(f"Downloaded PDF for paper {paper_id} to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error downloading PDF for paper {paper_id}: {str(e)}")
            raise
