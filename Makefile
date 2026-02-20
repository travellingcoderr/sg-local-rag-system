# sg-local-rag-system – Makefile
# Usage: make [target]. Run 'make help' for targets.

PYTHON  ?= python3
VENV    := .venv
BIN     := $(VENV)/bin
PIP     := $(BIN)/pip
STREAMLIT := $(BIN)/streamlit

.PHONY: help venv install install-dev run run-docker \
	download-embedding download-embedding-hf \
	docker-up docker-down docker-build \
	opensearch-up opensearch-down \
	check env clean

# Default target
help:
	@echo "sg-local-rag-system – available targets:"
	@echo ""
	@echo "  make help                  - show this help"
	@echo "  make venv                 - create virtual environment (.venv)"
	@echo "  make install              - install dependencies (requires venv)"
	@echo "  make run                  - run Streamlit app (Welcome.py)"
	@echo "  make run-docker           - run app + Ollama via docker compose"
	@echo "  make download-embedding   - download embedding model (sentence-transformers, full)"
	@echo "  make download-embedding-hf - download embedding model (huggingface_hub only, smaller)"
	@echo "  make docker-up            - start app + Ollama containers"
	@echo "  make docker-down          - stop app + Ollama containers"
	@echo "  make docker-build         - build app Docker image"
	@echo "  make opensearch-up        - start OpenSearch + Dashboards (standalone Docker)"
	@echo "  make opensearch-down      - stop OpenSearch + Dashboards"
	@echo "  make check                - sanity check (imports)"
	@echo "  make env                  - copy .env.example to .env if missing"
	@echo "  make clean                - remove __pycache__, .pyc, cache"
	@echo ""

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	@echo "Activate with: source $(BIN)/activate"

# Install dependencies (assumes venv exists)
install: $(VENV)/pyvenv.cfg
	$(PIP) install -r requirements.txt
	@echo "Done. Run 'make run' to start the app."

# Install with dev extras (if you add a dev-requirements later)
install-dev: install
	@echo "Dev install complete."

# Run Streamlit app locally (expects venv and install)
run: $(VENV)/pyvenv.cfg
	$(STREAMLIT) run Welcome.py

# Run via Docker Compose (app + Ollama)
run-docker: docker-up
	@echo "App: http://localhost:8501  Ollama: http://localhost:11434"

# Download embedding model (full: sentence-transformers, downloads model)
download-embedding: $(VENV)/pyvenv.cfg
	$(BIN)/python scripts/download_embedding_model.py
	@echo "Set EMBEDDING_MODEL_PATH=embedding_model in .env for faster startup."

# Download embedding model (hf only: huggingface_hub, no full model load)
download-embedding-hf: $(VENV)/pyvenv.cfg
	$(BIN)/python scripts/download_embedding_model_hf.py
	@echo "Set EMBEDDING_MODEL_PATH=embedding_model in .env for faster startup."

# Docker Compose: app + Ollama
docker-up:
	docker compose up -d
	@echo "App: http://localhost:8501"

docker-down:
	docker compose down

docker-build:
	docker compose build

# Standalone OpenSearch + Dashboards (for RAG; see docs/PREREQUISITES.md)
opensearch-up:
	@if docker ps -a -q -f name=^opensearch$$ | grep -q .; then \
	  echo "Starting existing OpenSearch container..."; docker start opensearch; \
	else \
	  echo "Creating OpenSearch container..."; \
	  docker run -d --name opensearch \
	    -p 9200:9200 -p 9600:9600 \
	    -e "discovery.type=single-node" \
	    -e "DISABLE_SECURITY_PLUGIN=true" \
	    opensearchproject/opensearch:2.11.0; \
	fi
	@if docker ps -a -q -f name=^opensearch-dashboards$$ | grep -q .; then \
	  echo "Starting existing OpenSearch Dashboards container..."; docker start opensearch-dashboards; \
	else \
	  echo "Creating OpenSearch Dashboards container..."; \
	  docker run -d --name opensearch-dashboards \
	    -p 5601:5601 \
	    --link opensearch:opensearch \
	    -e "OPENSEARCH_HOSTS=http://opensearch:9200" \
	    -e "DISABLE_SECURITY_DASHBOARDS_PLUGIN=true" \
	    opensearchproject/opensearch-dashboards:2.11.0; \
	fi
	@echo "OpenSearch: http://localhost:9200  Dashboards: http://localhost:5601"
	@echo "Create hybrid search pipeline: see docs/PREREQUISITES.md section 7."

opensearch-down:
	-docker stop opensearch-dashboards opensearch 2>/dev/null
	-docker rm opensearch-dashboards opensearch 2>/dev/null
	@echo "OpenSearch containers stopped and removed."

# Sanity check (imports)
check: $(VENV)/pyvenv.cfg
	$(BIN)/python -c "\
import streamlit; import sentence_transformers; import opensearchpy; import ollama; \
print('Streamlit:', streamlit.__version__); print('Sentence Transformers: OK'); \
print('OpenSearch client: OK'); print('Ollama client: OK');"

# Copy .env.example to .env if .env does not exist
env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; else echo ".env already exists"; fi

# Remove Python cache and bytecode
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean done."

# Ensure venv exists (used by targets that need it)
$(VENV)/pyvenv.cfg:
	@if [ ! -d $(VENV) ]; then echo "Run 'make venv' first."; exit 1; fi
