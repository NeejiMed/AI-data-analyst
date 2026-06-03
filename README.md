# AI Data Analyst

> A production-grade AI-powered analytics platform that accepts business questions in plain English and returns insights, SQL queries, statistical analysis, visualizations, and executive reports.

<!-- SCREENSHOT: Full application screenshot showing the Streamlit frontend with a question typed and results displayed. Place this at the top of the README for maximum visual impact. Suggested filename: docs/screenshots/hero.png -->
![AI Data Analyst Platform](docs/screenshots/hero.png)

## Live Demo

| Service | URL |
|---|---|
| Frontend | https://ai-data-analyst-frontend.onrender.com |
| API | https://ai-data-analyst-api.onrender.com |
| API Docs | https://ai-data-analyst-api.onrender.com/docs |

> **Note:** The free tier on Render spins down after 15 minutes of inactivity. The first request after a cold start takes 30–60 seconds. This is expected behavior for free-tier hosting.

---

## What It Does

Type any business question in plain English. The platform:

1. Classifies your intent (sales trend, segmentation, SQL query, anomaly investigation)
2. Queries the database automatically using a validated SQL agent
3. Computes KPIs, trends, and anomalies using a statistical analytics engine
4. Retrieves relevant business context from a knowledge base (RAG)
5. Generates natural language insights using Llama 3.3 70B
6. Produces interactive Plotly charts
7. Generates a downloadable Markdown/PDF report

### Example Questions

- *"Analyze monthly sales trends and explain anomalies"*
- *"Why did revenue decrease in Q2?"*
- *"Generate customer segmentation insights"*
- *"Compare regional performance"*
- *"What is the total revenue by product category?"*
- *"Show me the top 10 customers by total spend"*

---

## Screenshots

### Chat Interface
<!-- SCREENSHOT: The Streamlit chat interface with a question typed in the chat input and the conversation history showing the AI response summary. Suggested filename: docs/screenshots/chat_interface.png -->
![Chat Interface](docs/screenshots/chat_interface.png)

### Executive Summary Tab
<!-- SCREENSHOT: The Summary tab showing the executive summary text, positive signals, and risk factors after running a sales trend analysis. Suggested filename: docs/screenshots/summary_tab.png -->
![Executive Summary](docs/screenshots/summary_tab.png)

### Key Insights Tab
<!-- SCREENSHOT: The Insights tab showing the colored insight cards (red for critical, yellow for warning, green for info) with titles, explanations, and recommended actions. Suggested filename: docs/screenshots/insights_tab.png -->
![Key Insights](docs/screenshots/insights_tab.png)

### Interactive Charts
<!-- SCREENSHOT: The Charts tab showing the revenue trend line chart with the red diamond anomaly markers visible on October and December 2025. Suggested filename: docs/screenshots/charts_revenue_trend.png -->
![Revenue Trend Chart](docs/screenshots/charts_revenue_trend.png)

<!-- SCREENSHOT: The quarterly trend chart showing the dual-axis bar and line chart with revenue bars and growth rate line. Suggested filename: docs/screenshots/charts_quarterly.png -->
![Quarterly Performance](docs/screenshots/charts_quarterly.png)

### KPI Dashboard
<!-- SCREENSHOT: The KPI gauges showing gross margin (green, above target), refund rate (red, above target), and average order value indicators. Suggested filename: docs/screenshots/kpi_dashboard.png -->
![KPI Dashboard](docs/screenshots/kpi_dashboard.png)

### SQL Query Results
<!-- SCREENSHOT: The Data tab after asking "What is the total revenue by product category?" showing the generated SQL query in the expander and the results dataframe below. Suggested filename: docs/screenshots/sql_results.png -->
![SQL Query Results](docs/screenshots/sql_results.png)

### Customer Segmentation
<!-- SCREENSHOT: The Charts tab after asking for customer segmentation insights, showing the horizontal bar chart with RFM segments (Champions, Loyal, Promising, At Risk, Lost) and their customer counts and average revenue. Suggested filename: docs/screenshots/segmentation.png -->
![Customer Segmentation](docs/screenshots/segmentation.png)

### API Documentation
<!-- SCREENSHOT: The FastAPI /docs page showing the /query, /health, and /metrics endpoints with the interactive Swagger UI. Suggested filename: docs/screenshots/api_docs.png -->
![API Documentation](docs/screenshots/api_docs.png)

### CI/CD Pipeline
<!-- SCREENSHOT: The GitHub Actions tab showing a successful pipeline run with all three jobs (Lint, Tests, Docker Build) showing green checkmarks. Suggested filename: docs/screenshots/ci_pipeline.png -->
![CI/CD Pipeline](docs/screenshots/ci_pipeline.png)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│         Chat interface · Charts · Report download            │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                            │
│         /query · /health · /metrics · Middleware             │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              Agentic Workflow Orchestrator                    │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Intent    │  │  SQL Agent   │  │ Analytics Engine │   │
│  │ Classifier  │  │  NL → SQL    │  │ KPIs · Trends    │   │
│  │ Groq LLM   │  │  Validated   │  │ Anomalies · RFM  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │     RAG     │  │LLM Insights  │  │  Visualization   │   │
│  │  Pipeline   │  │ Groq Llama   │  │     Plotly       │   │
│  │  ChromaDB   │  │  3.3 70B     │  │  HTML + PNG      │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Report Engine                          │    │
│  │         Markdown · PDF · Download                   │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      Data Layer                              │
│  SQLite / PostgreSQL  │  ChromaDB  │  Redis (optional)       │
│  SQLAlchemy ORM       │  Embeddings│  Query cache            │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Chat UI and analytics dashboard |
| Backend | FastAPI + Python 3.11 | REST API and request routing |
| LLM | Groq API — Llama 3.3 70B | Intent classification, SQL generation, insights |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Local, free, no API key required |
| Vector DB | ChromaDB | RAG knowledge base retrieval |
| Analytics | Pandas + Polars + NumPy + SciPy | KPI computation, statistical analysis |
| Visualization | Plotly | Interactive charts and KPI gauges |
| Database | SQLite (dev) / PostgreSQL (prod) | Structured business data |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Logging | structlog | Structured JSON logging |
| CI/CD | GitHub Actions | Lint, test, Docker build on every push |
| Deployment | Render | Free-tier cloud hosting with HTTPS |
| Containers | Docker + Docker Compose | Reproducible environments |

---

## Project Structure

```
ai-data-analyst/
├── app/
│   ├── agents/              # Agentic workflow components
│   │   ├── intent_classifier.py   # LLM-based intent routing
│   │   ├── sql_agent.py           # NL-to-SQL with safety validation
│   │   ├── query_validator.py     # SQL injection prevention
│   │   ├── schema_inspector.py    # Dynamic schema extraction
│   │   ├── workflow.py            # Main orchestrator
│   │   └── response.py            # Unified response model
│   ├── analytics/           # Statistical analytics engine
│   │   ├── engine.py              # Main analytics orchestrator
│   │   ├── kpi.py                 # Revenue KPI computation
│   │   ├── trends.py              # Monthly/quarterly trend analysis
│   │   ├── anomaly.py             # Z-score anomaly detection
│   │   └── segmentation.py        # RFM customer segmentation
│   ├── core/                # Application configuration
│   │   ├── config.py              # Pydantic settings management
│   │   ├── logging.py             # Structured logging setup
│   │   └── observability/         # Metrics and middleware
│   ├── data/                # Data layer
│   │   ├── database.py            # SQLAlchemy engine and sessions
│   │   └── models/                # SQLAlchemy ORM models
│   ├── llm/                 # LLM integration layer
│   │   ├── client.py              # Groq API client with retry logic
│   │   ├── prompts.py             # Prompt engineering templates
│   │   ├── parser.py              # Structured output parsing
│   │   └── schemas.py             # Pydantic output schemas
│   ├── rag/                 # RAG pipeline
│   │   ├── pipeline.py            # RAG orchestrator
│   │   ├── embeddings.py          # Sentence-transformers embeddings
│   │   ├── vectorstore.py         # ChromaDB operations
│   │   ├── retrieval.py           # Document ingestion and chunking
│   │   └── knowledge_base/        # Markdown knowledge documents
│   ├── reports/             # Report generation engine
│   │   ├── builder.py             # Report composition
│   │   ├── markdown_renderer.py   # Markdown export
│   │   └── pdf_renderer.py        # PDF export via reportlab
│   ├── visualization/       # Chart generation
│   │   ├── charts.py              # Plotly chart functions
│   │   └── engine.py              # Visualization orchestrator
│   └── main.py              # FastAPI application entry point
├── frontend/
│   ├── main.py              # Streamlit application
│   ├── components.py        # Reusable UI components
│   └── styles.py            # Custom CSS
├── tests/
│   ├── unit/                # Unit tests (no external dependencies)
│   └── integration/         # Integration tests (API endpoints)
├── scripts/
│   ├── seed_data.py         # Database seeding with synthetic data
│   ├── startup.py           # Production startup script
│   └── verify_data.py       # Data verification utility
├── docs/
│   ├── architecture/        # System design documentation
│   └── decisions/           # Architecture Decision Records (ADRs)
├── .github/workflows/       # GitHub Actions CI/CD
├── docker/                  # Service-specific Dockerfiles
├── Dockerfile               # API service Docker image
├── docker-compose.yml       # Local development orchestration
├── render.yaml              # Render deployment configuration
├── requirements.txt         # Pinned Python dependencies
└── pyproject.toml           # Tool configuration (ruff, pytest)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com) (no credit card required)
- Git

### Local Setup

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/ai-data-analyst.git
cd ai-data-analyst
```

**2. Create a virtual environment and install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables**

```bash
cp .env.example .env
```

Open `.env` and add your Groq API key:

```bash
GROQ_API_KEY=your-groq-api-key-here
```

**4. Initialize the database and seed sample data**

```bash
python scripts/startup.py
```

This creates the database schema, seeds 18 months of synthetic business data (~6,600 orders), and initializes the RAG knowledge base.

**5. Start the API**

```bash
uvicorn app.main:app --reload
```

API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**6. Start the frontend**

In a second terminal:

```bash
streamlit run frontend/main.py
```

Frontend is available at `http://localhost:8501`.

### Docker Setup

Run both services with a single command:

```bash
docker-compose up --build
```

---

## API Reference

### `POST /query`

The main analytics endpoint. Accepts a business question and returns a complete AI analysis.

**Request:**
```json
{
  "question": "Analyze monthly sales trends and explain anomalies"
}
```

**Response:**
```json
{
  "question": "Analyze monthly sales trends and explain anomalies",
  "intent": "anomaly_investigation",
  "success": true,
  "executive_summary": "...",
  "insights": [...],
  "positive_signals": [...],
  "risk_factors": [...],
  "recommended_actions": [...],
  "chart_paths": {...},
  "report_paths": {...},
  "processing_time_ms": 4200
}
```

### `GET /health`

Returns the health status of all system components.

```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "healthy"},
    "vector_store": {"status": "healthy", "document_count": 3},
    "llm": {"status": "healthy", "model": "llama-3.3-70b-versatile"}
  }
}
```

### `GET /metrics`

Returns aggregated application metrics.

```json
{
  "uptime_seconds": 3600,
  "llm": {
    "total_calls": 42,
    "total_tokens": 58000,
    "avg_latency_ms": 1800
  },
  "workflows": {
    "total_runs": 15,
    "success_rate_pct": 100.0,
    "intent_distribution": {
      "sales_trend": 8,
      "sql_query": 4,
      "segmentation": 3
    }
  }
}
```

---

## Key Engineering Decisions

### Why no LangChain?
We build the orchestration layer from scratch. This means more boilerplate but complete transparency into what the system does at every step. You can read every line of `app/agents/workflow.py` and understand exactly how the agent works.

### Why Groq instead of OpenAI?
Groq provides a genuinely free API with no credit card requirement, running Llama 3.3 70B at fast inference speeds. The client uses the OpenAI-compatible API format — swapping providers requires changing two config values.

### Why SQLite instead of PostgreSQL?
SQLite is file-based, requires zero infrastructure, and works identically on local and cloud environments at our scale. The codebase is designed to switch to PostgreSQL by changing one environment variable.

### Why ChromaDB instead of Pinecone?
ChromaDB is open-source, runs locally, requires no API key, and is trivially containerized. For a portfolio project that needs to be deployable on a free tier, this is the correct trade-off.

### Why Streamlit instead of React?
Streamlit lets us ship a rich, interactive analytics UI entirely in Python — the same language as the backend — without maintaining a separate frontend codebase. For an AI analytics portfolio project this is the right choice.

---

## Security

The SQL generation agent enforces multiple security layers:

- **Read-only enforcement** — only `SELECT` statements are permitted, checked in code not just prompts
- **Schema-grounded generation** — the LLM only knows about tables and columns that actually exist
- **Forbidden keyword blocking** — `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE` are all blocked
- **System table protection** — queries against `sqlite_master`, `information_schema`, and similar are blocked
- **UNION injection prevention** — `UNION SELECT` patterns are blocked
- **Automatic row limits** — all queries without a `LIMIT` clause have one added automatically
- **Stacked query prevention** — multiple statements separated by semicolons are blocked

---

## Extending the Platform

### Adding domain knowledge to the RAG pipeline

Create a new Markdown file in `app/rag/knowledge_base/`:

```markdown
# Your Business Context

## Your KPI Definitions
...

## Your Business Rules
...
```

Then re-run ingestion:

```bash
python -c "
from app.rag.retrieval import ingest_knowledge_base
ingest_knowledge_base()
"
```

The next query will automatically retrieve from your new document.

### Connecting real data

Point `DATABASE_URL` in your `.env` at a real PostgreSQL database:

```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Update `app/data/models/business.py` if your schema differs from the default, then update the analytics queries in `app/analytics/` to match your column names.

### Adding a new analysis type

1. Add a new intent to `QueryIntent` in `app/agents/intent_classifier.py`
2. Add a new pipeline method to `AnalyticsWorkflow` in `app/agents/workflow.py`
3. Add analytics computation to `app/analytics/engine.py`
4. Add prompt templates to `app/llm/prompts.py`

---

## CI/CD Pipeline

Every push to `develop` or `main` triggers three parallel jobs:

```
Push
 ├── Lint (ruff check + ruff format)
 ├── Tests (pytest unit + integration)
 └── Docker Build (build image + health check)
```

The pipeline is defined in `.github/workflows/ci.yml`. Tests run without any external API calls — all LLM dependencies are mocked.

---

## Roadmap

- [ ] PostgreSQL support for production data persistence
- [ ] Redis caching layer for repeated queries
- [ ] Multi-tenant support with data isolation
- [ ] Additional chart types (scatter, heatmap, funnel)
- [ ] Scheduled report generation
- [ ] Webhook support for report delivery
- [ ] Fine-tuned embedding model for domain-specific retrieval
- [ ] Evaluation framework for LLM output quality

---

## License

MIT License. See `LICENSE` for details.

---

## Author

Built as a production-grade portfolio project demonstrating LLM engineering, RAG architecture, agentic workflows, analytics pipelines, and MLOps practices.

**Tech demonstrated:** FastAPI · Streamlit · Groq API · ChromaDB · SQLAlchemy · Plotly · Docker · GitHub Actions · Render
