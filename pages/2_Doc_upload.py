"""
Upload Documents page: upload PDFs, extract text, chunk, embed, and index into OpenSearch.
Documents are then searchable for RAG in the Chatbot (when RAG is enabled).
"""
import logging
import os
import time
from typing import TYPE_CHECKING

import streamlit as st

from src.constants import OPENSEARCH_INDEX, TEXT_CHUNK_SIZE
from src.utils import setup_logging

# Lazy imports: only load heavy dependencies when the page is actually rendered
# This prevents Streamlit from importing them during page discovery at startup
if TYPE_CHECKING:
    from PyPDF2 import PdfReader

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Upload Documents", page_icon="📄", layout="centered")

st.markdown(
    """
    <style>
    body { background-color: #f0f8ff; color: #002B5B; }
    .sidebar .sidebar-content { background-color: #006d77; color: white; padding: 20px; border-right: 2px solid #003d5c; }
    .sidebar h2, .sidebar h4 { color: white; }
    .block-container { background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); }
    .footer-text { font-size: 1.1rem; font-weight: bold; color: black; text-align: center; margin-top: 10px; }
    .stButton button { background-color: #118ab2; color: white; border-radius: 5px; padding: 10px 20px; font-size: 16px; }
    .stButton button:hover { background-color: #07a6c2; color: white; }
    .stButton.delete-button button { background-color: #e63946; color: white; font-size: 14px; }
    .stButton.delete-button button:hover { background-color: #ff4c4c; }
    h1, h2, h3, h4 { color: #006d77; }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_path = "images/purpleai.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=220)
else:
    st.sidebar.markdown("### Logo Placeholder")
    logger.warning("Logo not found, displaying placeholder.")

st.sidebar.markdown(
    "<h2 style='text-align: center;'>Upload Documents</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<h4 style='text-align: center;'>Your Document Assistant</h4>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    """
    <div class="footer-text">
        © 2026 Purple AI
    </div>
    """,
    unsafe_allow_html=True,
)


def save_uploaded_file(uploaded_file) -> str:
    """Save an uploaded file to uploaded_files/ and return its path."""
    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logger.info(f"File '{uploaded_file.name}' saved to '{file_path}'.")
    return file_path


def render_upload_page() -> None:
    """
    Renders the document upload page: load embedding model, connect to OpenSearch,
    list indexed documents, allow upload (PDF → text → chunks → embeddings → bulk index)
    and delete (from disk + OpenSearch).
    """
    # Lazy imports: only load when page is rendered (not during Streamlit page discovery)
    from PyPDF2 import PdfReader
    
    from src.embeddings import generate_embeddings, get_embedding_model
    from src.ingestion import (
        bulk_index_documents,
        create_index,
        delete_documents_by_document_name,
    )
    from src.opensearch import get_opensearch_client
    from src.utils import chunk_text_by_characters
    
    st.title("Upload Documents")

    # --- Load embedding model (can be slow on first run: downloads from Hugging Face) ---
    model_loading_placeholder = st.empty()
    if "embedding_models_loaded" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner("🔄 Loading embedding model... (First time: downloading ~400MB from Hugging Face, this may take 1-2 minutes)"):
                try:
                    get_embedding_model()
                    st.session_state["embedding_models_loaded"] = True
                    logger.info("Embedding models loaded.")
                except Exception as e:
                    logger.exception("Failed to load embedding model")
                    st.error(
                        "Could not load the embedding model. "
                        "If using a Hugging Face model name, check your network. "
                        "For a local model, run `python scripts/download_embedding_model_hf.py` and set "
                        "`EMBEDDING_MODEL_PATH=embedding_model` in `.env`."
                    )
                    model_loading_placeholder.empty()
                    return
        model_loading_placeholder.empty()

    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)

    # --- Connect to OpenSearch (fails fast if OpenSearch is not running) ---
    try:
        with st.spinner("Connecting to OpenSearch..."):
            client = get_opensearch_client()
        index_name = OPENSEARCH_INDEX
        create_index(client)
    except Exception as e:
        logger.warning(f"OpenSearch connection failed: {e}")
        st.warning(
            "**OpenSearch is not available.** Document upload and search require OpenSearch. "
            "Start OpenSearch (e.g. Docker or local install) at the configured host/port, then refresh this page. "
            "See docs/PREREQUISITES.md and docs/DOCKER.md for setup."
        )
        st.info("Configured endpoint: see `OPENSEARCH_HOST` and `OPENSEARCH_PORT` in `.env` (default: localhost:9200).")
        return

    if "documents" not in st.session_state:
        st.session_state["documents"] = []

    # Load list of document names already in the index
    query = {
        "size": 0,
        "aggs": {"unique_docs": {"terms": {"field": "document_name", "size": 10000}}},
    }
    try:
        response = client.search(index=index_name, body=query)
        buckets = response["aggregations"]["unique_docs"]["buckets"]
        document_names = [b["key"] for b in buckets]
    except Exception as e:
        logger.warning(f"Could not list documents from OpenSearch: {e}")
        document_names = []

    logger.info("Retrieved document names from OpenSearch.")

    # Build session state documents from index + local files
    st.session_state["documents"] = []
    for document_name in document_names:
        file_path = os.path.join(upload_dir, document_name)
        if os.path.exists(file_path):
            try:
                reader = PdfReader(file_path)
                text = "".join([page.extract_text() or "" for page in reader.pages])
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
                text = ""
            st.session_state["documents"].append(
                {"filename": document_name, "content": text, "file_path": file_path}
            )
        else:
            st.session_state["documents"].append(
                {"filename": document_name, "content": "", "file_path": None}
            )
            logger.warning(f"File '{document_name}' does not exist locally.")

    if "deleted_file" in st.session_state:
        st.success(
            f"The file '{st.session_state['deleted_file']}' was successfully deleted."
        )
        del st.session_state["deleted_file"]

    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type="pdf",
        accept_multiple_files=True,
    )

    if uploaded_files:
        with st.spinner("Uploading and processing documents. Please wait..."):
            for uploaded_file in uploaded_files:
                if uploaded_file.name in document_names:
                    st.warning(
                        f"The file '{uploaded_file.name}' already exists in the index."
                    )
                    continue

                file_path = save_uploaded_file(uploaded_file)
                try:
                    reader = PdfReader(file_path)
                    text = "".join([page.extract_text() or "" for page in reader.pages])
                except Exception as e:
                    st.error(f"Could not read PDF {uploaded_file.name}: {e}")
                    continue

                if not text.strip():
                    st.warning(
                        f"No text extracted from '{uploaded_file.name}'. Skipping."
                    )
                    continue

                chunks = chunk_text_by_characters(
                    text, chunk_size=TEXT_CHUNK_SIZE, overlap=100
                )
                embeddings = generate_embeddings(chunks)

                documents_to_index = [
                    {
                        "doc_id": f"{uploaded_file.name}_{i}",
                        "text": chunk,
                        "embedding": emb,
                        "document_name": uploaded_file.name,
                    }
                    for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
                ]
                bulk_index_documents(documents_to_index)

                st.session_state["documents"].append(
                    {
                        "filename": uploaded_file.name,
                        "content": text,
                        "file_path": file_path,
                    }
                )
                document_names.append(uploaded_file.name)
                logger.info(f"File '{uploaded_file.name}' uploaded and indexed.")

        st.success("Files uploaded and indexed successfully!")

    if st.session_state["documents"]:
        st.markdown("### Uploaded Documents")
        with st.expander("Manage Uploaded Documents", expanded=True):
            for idx, doc in enumerate(st.session_state["documents"], 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(
                        f"{idx}. {doc['filename']} - {len(doc['content'])} characters extracted"
                    )
                with col2:
                    delete_btn = st.button(
                        "Delete",
                        key=f"delete_{doc['filename']}_{idx}",
                        help=f"Delete {doc['filename']}",
                    )
                    if delete_btn:
                        if doc.get("file_path") and os.path.exists(doc["file_path"]):
                            try:
                                os.remove(doc["file_path"])
                                logger.info(
                                    f"Deleted file '{doc['filename']}' from filesystem."
                                )
                            except OSError as e:
                                st.error(f"Could not delete file: {e}")
                        delete_documents_by_document_name(doc["filename"])
                        st.session_state["documents"].pop(idx - 1)
                        st.session_state["deleted_file"] = doc["filename"]
                        time.sleep(0.5)
                        st.rerun()


if __name__ == "__main__":
    if "documents" not in st.session_state:
        st.session_state["documents"] = []
    render_upload_page()
