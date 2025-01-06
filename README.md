# arXival 📚

a research paper answering engine focused on openly accessible ML papers. give it a query, get back ai-generated responses with citations and figures from relevant papers.

## what's under the hood 🔧

### data sources
- arxiv + semantic scholar api for paper metadata and pdfs
- paper content processed from pdfs using pymupdf

### tech stack
- **frontend**: next.js 15 + app router, tailwind, shadcn/ui
- **backend**: fastapi + uvicorn
- **vector store**: chromadb (running on cloud)
- **llm**: openai gpt 4o-mini
- **embeddings**: openai text-embedding-3-large
- **storage**: cloudflare r2 for extracted figures

## running locally 🚀

1. clone the repo:
```bash
git clone https://github.com/seatedro/arxival.git
cd arxival
```

2. set up backend:
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on windows
pip install -r requirements.txt
```

3. set up env vars:
```bash
# backend (.env in server/)
OPENAI_API_KEY=your_key
CHROMADB_TOKEN=your_token
CHROMADB_SERVER=your_server
R2_ENDPOINT=your_endpoint
R2_ACCESS_KEY_ID=your_key
R2_SECRET_ACCESS_KEY=your_key
```

4. start the backend:
```bash
python run.py
```

5. set up frontend:
```bash
cd ui
npm install
```

6. set up frontend env:
```bash
# frontend (.env in ui/)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

7. start the frontend:
```bash
npm run dev
```

8. (optional) ingest some papers:
```bash
cd ../server
python cli_batch.py --query "machine learning" --max-papers 50
```

hit up `http://localhost:3000` and you're good to go! 🎉
