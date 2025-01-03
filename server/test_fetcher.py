import asyncio
from ingestion.paper_fetcher import PaperFetcher
import json

async def test_paper_fetcher():
    fetcher = PaperFetcher()

    print("\n=== Testing metadata fetching ===")
    # test searching for recent AI papers
    papers = await fetcher.fetch_papers(query="transformers", max_results=2)
    print(f"\nFetched {len(papers)} papers:")
    print(json.dumps(papers[0], indent=2))

    print("\n=== Testing specific paper fetch ===")
    paper_id = "2005.14165"  # GPT-3 paper, no html
    print(f"\nTrying to fetch content for paper {paper_id}")
    content = await fetcher.fetch_paper_content(paper_id)

    print(f"\nContent source type: {content['source_type']}")
    print(f"Content URL: {content['url']}")

    # print first 500 chars if html, or file path if pdf
    if content['source_type'] == 'html':
        print("\nFirst 500 chars of HTML content:")
        print(content['content'][:500])
    else:
        print("\nPDF saved at:", content['content'])

    old_paper_id = "1706.03762"  # Attention Is All You Need, has html
    print(f"\nTrying to fetch content for paper {old_paper_id}")
    content = await fetcher.fetch_paper_content(old_paper_id)

    print(f"\nContent source type: {content['source_type']}")
    print(f"Content URL: {content['url']}")

    if content['source_type'] == 'html':
        print("\nFirst 500 chars of HTML content:")
        print(content['content'][:500])
    else:
        print("\nPDF saved at:", content['content'])

if __name__ == "__main__":
    asyncio.run(test_paper_fetcher())
