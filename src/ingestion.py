"""
OpenSearch index creation, bulk indexing, and delete-by-document-name for RAG.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from opensearchpy import OpenSearch, helpers

from src.constants import (
    ASSYMETRIC_EMBEDDING,
    EMBEDDING_DIMENSION,
    OPENSEARCH_INDEX,
)
from src.opensearch import get_opensearch_client
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def load_index_config() -> Dict[str, Any]:
    """Load index settings and mappings from src/index_config.json; set embedding dimension."""
    config_path = Path(__file__).resolve().parent / "index_config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    config["mappings"]["properties"]["embedding"]["dimension"] = EMBEDDING_DIMENSION
    logger.info("Index configuration loaded from src/index_config.json.")
    return config


def create_index(client: OpenSearch) -> None:
    """Create the OpenSearch index if it does not exist."""
    index_body = load_index_config()
    if not client.indices.exists(index=OPENSEARCH_INDEX):
        response = client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
        logger.info(f"Created index {OPENSEARCH_INDEX}: {response}")
    else:
        logger.info(f"Index {OPENSEARCH_INDEX} already exists.")


def bulk_index_documents(
    documents: List[Dict[str, Any]],
) -> Tuple[int, List[Any]]:
    """
    Index documents into OpenSearch in bulk.
    Each document must have: doc_id, text, embedding (array or ndarray), document_name.
    """
    actions = []
    client = get_opensearch_client()

    for doc in documents:
        doc_id = doc["doc_id"]
        emb = doc["embedding"]
        embedding_list = emb.tolist() if hasattr(emb, "tolist") else list(emb)
        document_name = doc["document_name"]
        prefixed_text = (
            f"passage: {doc['text']}" if ASSYMETRIC_EMBEDDING else doc["text"]
        )
        actions.append(
            {
                "_index": OPENSEARCH_INDEX,
                "_id": doc_id,
                "_source": {
                    "text": prefixed_text,
                    "embedding": embedding_list,
                    "document_name": document_name,
                },
            }
        )

    success, errors = helpers.bulk(client, actions)
    logger.info(
        f"Bulk indexed {len(documents)} documents into {OPENSEARCH_INDEX} with {len(errors)} errors."
    )
    return success, errors


def delete_documents_by_document_name(document_name: str) -> Dict[str, Any]:
    """Delete all documents in the index whose document_name matches."""
    client = get_opensearch_client()
    query = {"query": {"term": {"document_name": document_name}}}
    response = client.delete_by_query(index=OPENSEARCH_INDEX, body=query)
    logger.info(f"Deleted documents with name '{document_name}' from {OPENSEARCH_INDEX}.")
    return response
