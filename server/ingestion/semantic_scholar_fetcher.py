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
    BASE_SINGLE = "https://api.semanticscholar.org/graph/v1/paper"

    def __init__(self, min_citations: int = 100, year_from: int = 2017, year_to: int | None = None):
        self.min_citations = min_citations
        self.fields = [
                    "title", "abstract", "year", "authors", "openAccessPdf",
                    "citationCount", "venue", "publicationDate", "fieldsOfStudy",
                    "externalIds", "url"
                ]
        self.year_from = year_from
        self.year_to = year_to
        self.paper_cache = {}

    def _get_source_info(self, paper: Dict) -> Dict:
        """Extract paper source and format proper URL"""
        external_ids = paper.get('externalIds', {})

        # Try to identify source and get proper URL
        if 'ArXiv' in external_ids:
            return {
                'source': 'arxiv',
                'source_id': external_ids['ArXiv'],
                'pdf_url': f"https://arxiv.org/pdf/{external_ids['ArXiv']}.pdf",
                'paper_url': f"https://arxiv.org/abs/{external_ids['ArXiv']}",
            }
        elif 'DOI' in external_ids:
            return {
                'source': 'doi',
                'source_id': external_ids['DOI'],
                'pdf_url': paper['openAccessPdf']['url'] if 'openAccessPdf' in paper and paper['openAccessPdf'] else None,
                'paper_url': f'https://doi.org/{external_ids["DOI"]}'
            }
        else:
            # Fallback
            return {
                'source': 'other',
                'source_id': paper['paperId'],
                'pdf_url': paper['openAccessPdf']['url'] if 'openAccessPdf' in paper and paper['openAccessPdf'] else None,
                'paper_url': paper['url']
            }

    async def fetch_single_paper(self, paper_id: str) -> Dict:
        """Fetch single paper by ID"""
        try:
            params = {
                'fields': ','.join(self.fields),
            }
            papers = []
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.BASE_SINGLE}/{paper_id}", params=params) as resp:
                    if resp.status != 200:
                        logger.error(f"API error: {resp.status}")
                        return {}

                    data = await resp.json()
                    paper = self._process_paper(data)
                    if paper:
                        self.paper_cache[paper['id']] = paper
                        papers.append(paper)

            return papers[0]

        except Exception as e:
            logger.error(f"Error fetching paper {paper_id}: {str(e)}")
            return {}

    async def fetch_papers(self,
                          query: Optional[str] = "",
                          paper_ids: Optional[List[str]] = None,
                          field: Optional[str] = "Computer Science",
                          max_results: int = 100) -> List[Dict]:
        """
        Fetch papers from Semantic Scholar based on query or paper IDs.
        Returns list of paper metadata + content dicts.
        """
        try:
            params = {
                'query': query or '',
                'limit': min(max_results, 1000),
                'fields': ','.join(self.fields),
                'sort': 'citationCount:desc',
                # 'openAccessPdf': '',
                'year': f'{self.year_from}' if not self.year_to else f'{self.year_from}-{self.year_to}',
                'fieldsOfStudy': field,
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

            return papers[:max_results]

        except Exception as e:
            logger.error(f"Error fetching papers: {str(e)}")
            raise

    def _process_paper(self, paper: Dict) -> Optional[Dict]:
        """Process raw API response into standard format"""
        try:


            source_info = self._get_source_info(paper)

            if not paper.get('openAccessPdf') and source_info.get("source") != "arxiv":
                return None

            if os.path.exists(f"./papers/{paper['paperId']}.pdf"):
                logger.info(f"Paper {paper['paperId']} {paper['title']} already downloaded, skipping...")
                return None


            return {
                "id": paper.get('paperId'),
                "title": paper.get('title'),
                "abstract": paper.get('abstract'),
                "authors": [author['name'] for author in paper.get('authors', [])],
                "categories": paper.get('fieldsOfStudy', []),
                "published": paper.get('publicationDate') or f"{paper.get('year')}-01-01",
                "updated": paper.get('publicationDate') or f"{paper.get('year')}-01-01",
                "pdf_url": source_info['pdf_url'],
                "paper_url": source_info['paper_url'],
                "citation_count": paper.get('citationCount'),
                "venue": paper.get('venue'),
                "source": source_info['source'],
                "source_id": source_info['source_id'],
                "external_ids": paper.get('externalIds', {})
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
                "url": paper['pdf_url'],
                "paper_url": paper['paper_url'],
                "source": paper['source'],
                "source_id": paper['source_id']
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


            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(pdf_url) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Failed to download PDF: {resp.status}")

                    with open(filepath, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

            return filepath

        except Exception as e:
            logger.error(f"Error downloading PDF for paper {paper_id}: {str(e)}")
            raise
