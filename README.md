# ResearchRanger - Autonomous Research Agent with RAG and Citation Tracing

A powerful research assistant that helps researchers, students, and product teams ingest documents (PDFs, web pages, notes), answer questions with source citations, and export referenceable summaries.

## Features

- 📄 **Document Ingestion**: Upload PDFs, webpages, and markdown files
- 🔍 **Intelligent QA**: Ask questions and get answers with precise citations
- 📚 **Citation Tracking**: Page/paragraph level citation provenance
- 📝 **Export Capabilities**: Generate Markdown summaries and BibTeX references
- 🎯 **Evidence-Based Answers**: Every answer includes source snippets and metadata
- ⚡ **Background Processing**: Asynchronous document ingestion pipeline

## Tech Stack

### Backend
- **Framework**: FastAPI
- **RAG**: LangChain
- **Workers**: Celery + Redis
- **Database**: PostgreSQL
- **Vector DB**: Chroma (local) / Pinecone (production)
- **Storage**: S3-compatible (local filesystem for dev)
- **PDF Parsing**: PyMuPDF

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: React with streaming chat interface
- **Styling**: Tailwind CSS

## Project Structure

```
.
├── backend/          # FastAPI application
├── frontend/         # Next.js application
├── workers/          # Celery workers
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL
- Redis

### Local Development

1. **Clone and setup backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Setup frontend**:
```bash
cd frontend
npm install
```

3. **Start services** (using Docker Compose):
```bash
docker-compose up -d
```

4. **Run migrations**:
```bash
cd backend
alembic upgrade head
```

5. **Start backend**:
```bash
cd backend
uvicorn app.main:app --reload
```

6. **Start frontend**:
```bash
cd frontend
npm run dev
```

## Architecture

### Ingestion Flow
1. User uploads document → API stores file
2. Celery worker extracts text (PDF/HTML/MD)
3. Document is chunked with overlap and metadata
4. Embeddings generated and stored in vector DB
5. Metadata (file, page, paragraph, offsets) linked to chunks

### QA Flow
1. User asks question → Query embedded
2. Top-K similar chunks retrieved from vector DB
3. Evidence-aware prompt constructed with source snippets
4. LLM generates answer with inline citations
5. Citations parsed and linked back to source documents
6. Response streamed to frontend with source highlights

## License

MIT

