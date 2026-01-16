# Setup Guide - ResearchRanger

Complete setup instructions for running ResearchRanger locally.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for PostgreSQL and Redis)
- OpenAI API key

## Step 1: Clone and Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Setup Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Step 3: Start Infrastructure Services

```bash
# From project root, start PostgreSQL and Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

## Step 4: Configure Environment

Create a `.env` file in the backend directory:

```bash
# Copy example
cp .env.example .env

# Edit .env and add your OpenAI API key
# DATABASE_URL=postgresql://research:research@localhost:5432/researchranger
# OPENAI_API_KEY=your-openai-api-key-here
```

Create a `.env.local` file in the frontend directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Step 5: Run Database Migrations

```bash
cd backend

# Make sure virtual environment is activated
source venv/bin/activate

# Run migrations
alembic upgrade head
```

## Step 6: Start Backend Server

```bash
cd backend

# Make sure virtual environment is activated
source venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
./run.sh
```

## Step 7: Start Celery Worker (Background Processing)

Open a new terminal:

```bash
cd backend
source venv/bin/activate

# Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info
```

## Step 8: Start Frontend

Open another terminal:

```bash
cd frontend

# Start Next.js dev server
npm run dev
```

## Step 9: Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## First Use

1. Register a new account at http://localhost:3000/login
2. Create a project
3. Upload PDFs or documents
4. Wait for processing (check document status)
5. Ask questions in the Chat interface

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL in `.env`
- Verify database exists: `docker-compose exec postgres psql -U research -d researchranger`

### Celery Worker Not Processing
- Ensure Redis is running: `docker-compose ps`
- Check CELERY_BROKER_URL in `.env`
- Restart worker: `celery -A app.workers.celery_app worker --loglevel=info`

### Document Not Processing
- Check Celery worker logs
- Verify document status in UI
- Check backend logs for errors

### OpenAI API Errors
- Verify OPENAI_API_KEY is set in `.env`
- Check API key validity
- Ensure sufficient API credits

## Development Tips

- Backend auto-reloads on file changes (with --reload flag)
- Frontend hot-reloads automatically in dev mode
- Use `docker-compose logs -f` to view service logs
- Reset database: `docker-compose down -v && docker-compose up -d && alembic upgrade head`

