"""
ChromaDB vector store wrapper.
Handles document storage, indexing, and semantic retrieval.
"""

import logging
from pathlib import Path

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.rag.embeddings import embed_text, embed_texts

logging.getLogger("chromadb").setLevel(logging.ERROR)

logger = structlog.get_logger()
settings = get_settings()

COLLECTION_NAME = "business_knowledge"


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Return a persistent ChromaDB client.
    Data survives restarts - stored at chroma_persist_dir.
    """
    persist_path = Path(settings.chroma_persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(persist_path), settings=ChromaSettings(anonymized_telemetry=False)
    )

    return client


def get_or_create_collection() -> chromadb.Collection:
    """Get existing collection or create if it doesn't exist."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
    return collection


def add_documents(documents: list[str], metadatas: list[dict], ids: list[str]) -> None:
    """
    Add documents to the vector store with their embeddings.
    Args:
        documents: raw text chunks to store
        metadatas: dicts with metadata for each document (e.g. source, timestamp)
        ids: unique string IDs for each document (e.g. "doc1", "doc2")
    """
    collection = get_or_create_collection()

    # Check for existing IDs to avoid duplicates
    existing = collection.get(ids=ids)
    existing_ids = set(existing["ids"])
    new_indices = [i for i, id in enumerate(ids) if id not in existing_ids]

    if not new_indices:
        logger.info("all_documents_already_indexed", count=len(ids))
        return

    new_docs = [documents[i] for i in new_indices]
    new_metas = [metadatas[i] for i in new_indices]
    new_ids = [ids[i] for i in new_indices]
    embeddings = embed_texts(new_docs)

    collection.add(
        documents=new_docs, embeddings=embeddings, metadatas=new_metas, ids=new_ids
    )

    logger.info("documents_indexed", count=len(new_docs))


def query_similar(
    query_text: str, n_results: int = 5, where: dict | None = None
) -> list[dict]:
    """
    Retrive semantically similar documents for a query.
    Args:
        query_text: user question or statement to find relevant documents for
        n_results: how many similar documents to return
        where: optional metadata filter (e.g. {"source": "sales_report_q1"})

    Returns:
        List of dicts with keys: "document", "metadata", "id", "similarity"
    """
    collection = get_or_create_collection()
    count = collection.count()

    if count == 0:
        logger.warning("no_documents_in_collection")
        return []

    query_embedding = embed_text(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, count),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i in range(len(results["ids"][0])):
        output.append(
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i],
            }
        )

    logger.info(
        "retrieval_performed", query_preview=query_text[:60], results_found=len(output)
    )

    return output


def get_collection_stats() -> dict:
    """Return stats about the vector store collection."""
    collection = get_or_create_collection()
    count = collection.count()
    return {
        "collection_name": COLLECTION_NAME,
        "document_count": count,
        "persist_dir": settings.chroma_persist_dir,
    }
