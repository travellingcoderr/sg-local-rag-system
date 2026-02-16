"""
Application configuration. Edit these values to match your environment and preferences.
See docs/PREREQUISITES.md step 10 for a full explanation of each variable.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (so it works no matter where you run the app from)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# -----------------------------------------------------------------------------
# Embedding model (for turning text into vectors / semantic search)
# -----------------------------------------------------------------------------

# Where to load the embedding model from. Two options:
#   - Hugging Face model name: the app will download it on first run (e.g. "sentence-transformers/all-mpnet-base-v2").
#   - Local folder path: after running scripts/download_embedding_model.py, set to "embedding_model" for faster startup.
EMBEDDING_MODEL_PATH = os.environ.get("EMBEDDING_MODEL_PATH", "sentence-transformers/all-mpnet-base-v2")

# Set to True only if using a model that uses different encodings for queries vs documents (e.g. some retrieval models). Leave False for standard Sentence Transformer models.
ASSYMETRIC_EMBEDDING = False

# Length of the vector produced by the embedding model. Must match the model you use:
#   - all-mpnet-base-v2  -> 768
#   - all-MiniLM-L6-v2   -> 384
#   - all-MiniLM-L12-v2  -> 384
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "768"))

# -----------------------------------------------------------------------------
# Document chunking
# -----------------------------------------------------------------------------

# Maximum number of characters per text chunk when splitting documents. Smaller values (e.g. 300) often improve retrieval precision but create more chunks; larger values keep more context per chunk. Tune based on your documents and LLM context window.
TEXT_CHUNK_SIZE = int(os.environ.get("TEXT_CHUNK_SIZE", "300"))

# -----------------------------------------------------------------------------
# LLM provider: ollama (local) | openai | gemini (prod)
# -----------------------------------------------------------------------------

# Which LLM to use. In prod set env: LLM_PROVIDER=openai or LLM_PROVIDER=gemini
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").lower().strip()

# Ollama (local / Docker)
OLLAMA_MODEL_NAME = os.environ.get("OLLAMA_MODEL_NAME", "llama3.2:1b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")  # in docker-compose use http://ollama:11434

# OpenAI (prod)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Google Gemini (prod)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

# -----------------------------------------------------------------------------
# Logging (you can change the path if you prefer)
# -----------------------------------------------------------------------------

LOG_FILE_PATH = "logs/app.log"

# -----------------------------------------------------------------------------
# OpenSearch (vector store / search backend)
# -----------------------------------------------------------------------------

# Host where OpenSearch is running. Use "localhost" when running OpenSearch on host; use service name (e.g. opensearch) in Docker.
OPENSEARCH_HOST = os.environ.get("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.environ.get("OPENSEARCH_PORT", "9200"))

# Name of the index where document chunks and embeddings are stored. The app will create this index if it does not exist. You usually do not need to change this unless you want to separate different projects.
OPENSEARCH_INDEX = "documents"
EMBEDDING_MODEL_PATH="embedding_model"