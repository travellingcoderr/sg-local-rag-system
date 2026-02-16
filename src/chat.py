"""
Chat: prompt → LLM → response. Backend is selected by LLM_PROVIDER (ollama | openai | gemini).
RAG: optionally retrieve context from OpenSearch and pass to LLM.
See src/llm.py for the actual provider implementations.
"""
import logging
from typing import List, Optional

from src.llm import ensure_model_pulled, generate_response_streaming
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def get_rag_context(query: str, top_k: int = 5) -> str:
    """
    Retrieve relevant document chunks from OpenSearch for the given query (hybrid search).
    Returns a string of concatenated chunk texts to use as context for the LLM, or empty string on failure.
    """
    try:
        from src.constants import OPENSEARCH_INDEX
        from src.embeddings import get_embedding_model
        from src.opensearch import get_opensearch_client, hybrid_search

        client = get_opensearch_client()
        if not client.indices.exists(index=OPENSEARCH_INDEX):
            return ""
        model = get_embedding_model()
        query_embedding = model.encode(query).tolist()
        hits = hybrid_search(query_text=query, query_embedding=query_embedding, top_k=top_k)
        if not hits:
            return ""
        parts = [hit["_source"]["text"].strip() for hit in hits if hit.get("_source", {}).get("text")]
        return "\n\n".join(parts) if parts else ""
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return ""


__all__ = ["ensure_model_pulled", "generate_response_streaming", "get_rag_context"]
