"""
Document ingestion, chuncks knowledge base files and indexes them.
Run once to populate the vector store, then periodically to add new documents.
"""

import re
from pathlib import Path

import structlog

from app.rag.vectorstore import add_documents, get_collection_stats

logger = structlog.get_logger()

KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"


def _categorize(source: str) -> str:
    """Infer document category from filename."""
    if "business_context" in source:
        return "business_context"
    elif "metrics" in source:
        return "metrics"
    elif "playbook" in source:
        return "playbook"
    return "general"


def chunk_markdown(
    text: str, source: str, chunk_size: int = 400, overlap: int = 50
) -> list[tuple[str, dict]]:
    """
    Split markdown text into overlapping chunks for indexing.

    Why overlap? A chunk boundary might split a sentence that contains
    the key concept being searched for. Overlapping windows ensure
    every sentence appears in at least one complete chunk.

    Returns:
        List of (chunk_text, metadata) tuples
    """
    # Split on markdown headers first to preserve section context
    sections = re.split(r"\n(#{1,3} .+)\n", text)

    chunks = []
    current_section = "general"
    current_text = ""

    for part in sections:
        if re.match(r"^#{1,3} ", part):
            # Save previous section as a chunk
            current_section = part.strip("# ").strip()
            continue
        current_text += " " + part.strip()

        # chunk when we exceed chunk_size words
        words = current_text.split()
        while len(words) > chunk_size:
            chunk = " ".join(words[:chunk_size])
            chunks.append(
                (
                    chunk,
                    {
                        "source": source,
                        "section": current_section,
                        "category": _categorize(source),
                    },
                )
            )
            words = words[overlap:]  # keep some overlap for context
        current_text = " ".join(words)

    # Add any remaining text as a final chunk
    if current_text.strip():
        chunks.append(
            (
                current_text.strip(),
                {
                    "source": source,
                    "section": current_section,
                    "category": _categorize(source),
                },
            )
        )

    return chunks


def ingest_knowledge_base() -> int:
    """
    ingest all markdown files from the knowledge base directory.
    idempotent - can be run multiple times without creating duplicates.
    Returns
        Number of chunks indexed
    """
    logger.info("starting_knowledge_base_ingestion")

    if not KNOWLEDGE_BASE_DIR.exists():
        logger.error("knowledge_base_dir_not_found", path=str(KNOWLEDGE_BASE_DIR))
        return 0

    md_files = list(KNOWLEDGE_BASE_DIR.glob("*.md"))
    if not md_files:
        logger.warning("no_markdown_files_found", path=str(KNOWLEDGE_BASE_DIR))
        return 0

    all_docs = []
    all_metas = []
    all_ids = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, source=md_file.name)

        for i, (chunk_text, metadata) in enumerate(chunks):
            doc_id = f"{md_file.stem}_chunk{i}"
            all_docs.append(chunk_text)
            all_metas.append(metadata)
            all_ids.append(doc_id)

        logger.info("file_chunked", file=str(md_file), chunk_count=len(chunks))

    add_documents(all_docs, all_metas, all_ids)
    stats = get_collection_stats()

    logger.info(
        "knowledge_base_ingestion_complete",
        total_chunks=len(all_docs),
        indexed=stats["document_count"],
    )
    return len(all_docs)
