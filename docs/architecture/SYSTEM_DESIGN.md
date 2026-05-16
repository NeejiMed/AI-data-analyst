# System Design — AI Data Analyst

## Overview
An end-to-end AI analytics platform that translates business questions
into structured data queries, performs statistical analysis, and returns
insights with visualizations and natural language explanations.

## Core Components

### 1. API Gateway (FastAPI)
- Entry point for all requests
- Handles auth, rate limiting, request validation
- Routes to the agentic orchestration layer

### 2. Agentic Orchestration
- Planner: decides which tools/agents to invoke
- Executor: runs tools in sequence or parallel
- Supports multi-step reasoning workflows

### 3. SQL Agent
- Converts natural language to SQL
- Validates and sanitizes generated queries
- Prevents SQL injection and hallucinated schema refs

### 4. Analytics Engine
- Statistical analysis with Pandas/Polars
- KPI computation
- Anomaly detection

### 5. RAG Pipeline
- Business context knowledge base
- ChromaDB vector store
- Semantic retrieval for domain context

### 6. Report + Visualization Engine
- Plotly chart generation
- Markdown/PDF report generation
- Executive summary composition

## Architecture Decision Records (ADRs)
See `docs/decisions/` for trade-off documentation.

## Data Flow
User Question → API → Orchestrator → [SQL Agent + Analytics + RAG]
→ LLM → Report Engine → Response
