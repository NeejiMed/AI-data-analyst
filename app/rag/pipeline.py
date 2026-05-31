"""
RAG pipeline, retrieves relevant context and formats it for LLM injection.
"""
import structlog

from app.rag.retrieval import ingest_knowledge_base
from app.rag.vectorstore import get_collection_stats, query_similar

logger = structlog.get_logger()

class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline.
    Retrieves domain knowledge relevant to a user query
    and formats it for injection into LLM prompts.
    """

    def __init__(self, auto_ingest: bool = True):
        """
        Args:
            auto_ingest: if True, checks if vector store is empty and triggers ingestion if needed
        """
        self._ingested = False
        if auto_ingest:
            self._ensure_ingested()

    def _ensure_ingested(self) -> None:
        """Ingest knowledge base if collection is empty."""
        stats = get_collection_stats()
        if stats["document_count"] == 0:
            logger.info("Vector_store_is_empty_Triggering_ingestion.")
            ingest_knowledge_base()
        else:
            logger.info("Vector_store_already_populated", document_count=stats["document_count"])
        self._ingested = True

    def retrieve(
            self,
            query: str,
            n_results: int = 4,
            category_filter: str | None = None
    ) -> list[dict]:
        """
        Retrieve relevant knowledge chunks for a user query.
        Args:
            query: user question or statement to find relevant documents for
            n_results: how many similar documents to return
            category_filter: optional filter to restrict retrieval to a specific category (e.g. "metrics")
        """
        where = {"category": category_filter} if category_filter else None
        return query_similar(query, n_results=n_results, where=where)

    def build_context(
            self,
            query: str,
            n_results: int = 4
    ) -> str:
        """"
        Retrieve and format knowledge base context for LLM injection.
        Returns:
            Formatted string ready to inject into LLM prompts
        """
        results = self.retrieve(query, n_results=n_results)
        if not results:
            return ""

        context_lines = [
            "RELEVANT BUSINESS CONTEXT:",
            "=" * 30,
            "The following domain knowledge is relevant to this query:",
            ""
        ]

        for i, result in enumerate(results, 1):
            score_pct = round(result["score"] * 100, 1)
            context_lines.append(
                f"[Context {i} — {result['metadata'].get('section', 'general')} "
                f"({score_pct}% relevance)]"
            )
            context_lines.append(result["document"])
            context_lines.append("")

        return "\n".join(context_lines)

    def get_stats(self) -> dict:
        """Return current vector store stats."""
        return get_collection_stats()
