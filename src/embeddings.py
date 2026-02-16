"""
Load embedding model and generate embeddings for text chunks (for RAG indexing and search).
"""
import logging
from typing import Any, List

import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

from src.constants import EMBEDDING_MODEL_PATH
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def get_embedding_model() -> SentenceTransformer:
    """
    Loads and caches the embedding model.
    """
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
    model = get_embedding_model()
    embeddings = [np.array(model.encode(chunk)) for chunk in chunks]
    logger.info(f"Generated embeddings for {len(chunks)} text chunks.")
    return embeddings
