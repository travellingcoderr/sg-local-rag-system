"""
Load embedding model and generate embeddings for text chunks (for RAG indexing and search).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List

import streamlit as st

from src.constants import EMBEDDING_MODEL_PATH
from src.utils import setup_logging

if TYPE_CHECKING:
    import numpy as np
    from sentence_transformers import SentenceTransformer

setup_logging()
logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def get_embedding_model() -> "SentenceTransformer":
    """
    Loads and caches the embedding model.
    sentence_transformers (and its deps: transformers, sklearn, joblib) are imported
    here so they are not loaded at module import time, avoiding import-order and
    atexit issues when Streamlit reloads pages.
    """
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading embedding model from path: {EMBEDDING_MODEL_PATH}")
    return SentenceTransformer(EMBEDDING_MODEL_PATH)


def generate_embeddings(chunks: List[str]) -> List[Any]:
    """
    Generates embeddings for a list of text chunks.

    Args:
        chunks: List of text chunks.

    Returns:
        List of embeddings (numpy arrays) for each chunk.
    """
    import numpy as np  # Lazy import: only load when actually generating embeddings
    
    model = get_embedding_model()
    embeddings = [np.array(model.encode(chunk)) for chunk in chunks]
    logger.info(f"Generated embeddings for {len(chunks)} text chunks.")
    return embeddings
