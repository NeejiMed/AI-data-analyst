# AI Data Analyst

A production-grade AI-powered analytics platform that accepts business questions
in plain English and returns insights, SQL queries, statistical analysis,
visualizations, and executive reports.

## Architecture
See `docs/architecture/` for system design documents.

## Quick Start
\```bash
docker-compose up --build
\```

## Tech Stack
- Backend: FastAPI + Python 3.11
- LLM: OpenAI API (GPT-4o)
- RAG: ChromaDB + OpenAI Embeddings
- Analytics: Pandas + Polars
- Visualization: Plotly
- Frontend: Streamlit
- DevOps: Docker + GitHub Actions