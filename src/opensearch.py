"""
OpenSearch client and hybrid search (text + vector) for RAG.
"""
import logging
from typing import Any, Dict, List

from opensearchpy import OpenSearch

from src.constants import OPENSEARCH_HOST, OPENSEARCH_INDEX, OPENSEARCH_PORT
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def get_opensearch_client() -> OpenSearch:
    """
    Initializes and returns an OpenSearch client.
    """
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        http_compress=True,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )
    logger.info("OpenSearch client initialized.")
    return client


def hybrid_search(
    query_text: str, query_embedding: List[float], top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Performs hybrid search (text match + vector similarity) using the nlp-search-pipeline.
    """
    client = get_opensearch_client()
    query_body = {
        "_source": {"exclude": ["embedding"]},
        "query": {
            "hybrid": {
                "queries": [
                    {"match": {"text": {"query": query_text}}},
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": top_k,
                            }
                        }
                    },
                ]
            }
        },
        "size": top_k,
    }
    response = client.search(
        index=OPENSEARCH_INDEX,
        body=query_body,
        search_pipeline="nlp-search-pipeline",
    )
    logger.info(f"Hybrid search completed for query '{query_text}' with top_k={top_k}.")
    return response["hits"]["hits"]
