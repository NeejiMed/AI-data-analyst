# ADR-001: Technology Stack Selection

**Date:** 2026-05-16  
**Status:** Accepted

## Context
We need to select a technology stack for an AI data analyst platform
that is production-grade, free to deploy, and showcases modern LLM engineering.

## Decision
- Backend: FastAPI (async, Pydantic, OpenAPI)
- LLM: OpenAI API (GPT-4o for reasoning, text-embedding-3-small for RAG)
- Vector DB: ChromaDB (local, open-source, Docker-friendly)
- Analytics: Pandas + Polars (Polars for large datasets)
- Frontend: Streamlit (Python-native, rapid iteration)
- Deployment: Docker Compose (local) + Render (cloud free tier)

## Alternatives Considered
- LangChain: Rejected — adds abstraction overhead and hides LLM mechanics
  we want to learn. We build our own orchestration.
- Kubernetes: Rejected — overengineering at this scale.
- Pinecone: Rejected — paid managed service, ChromaDB is portable.
- Next.js frontend: Possible future upgrade once Streamlit limits are hit.

## Consequences
- We write more boilerplate than LangChain would give us
- We learn the real mechanics of LLM orchestration
- We stay infrastructure-cost-zero for deployment