# sg-local-rag-system

Create a local RAG system that runs entirely on your machine—no cloud, no PII leaving your computer. This guide walks you through setup in small steps.

---

## What you’ll use

| Component | Role |
|----------|------|
| **Streamlit** | Web UI for uploading docs and chatting |
| **Sentence Transformers** | Turn text into vectors (embeddings) for semantic search |
| **OpenSearch** | Store and search those vectors (hybrid search) |
| **LLM** | Ollama (local), or OpenAI / Gemini (prod) for answers |
| **PyPDF2 / pytesseract / Pillow** | Read PDFs and images from your documents |

---

## Baby steps: get ready to run the app

### Step 0: Prerequisites

Install all required tools and runtimes before continuing. See **[docs/PREREQUISITES.md](docs/PREREQUISITES.md)** for detailed, step-by-step instructions for your OS.

- **Python 3.10+**
- **pip**
- **(Optional, for later)** Docker (for OpenSearch) and Tesseract (for OCR)

---

### Step 1: Get the code

Clone or use this repo as your base:

```bash
cd /path/to/sg-local-rag-system
```

---

### Step 2: Create a virtual environment (recommended)

Keeps this project’s packages separate from the rest of your system.

```bash
# Create a venv in the project folder
python3 -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows (Command Prompt):
# .venv\Scripts\activate.bat
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1
```

You should see something like `(.venv)` in your shell prompt.

---

### Step 3: Upgrade pip (optional but recommended)

```bash
pip install --upgrade pip
```

---

### Step 4: Install dependencies

From the project root (where `requirements.txt` is):

```bash
pip install -r requirements.txt
```

This installs Streamlit, sentence-transformers, PyTorch, OpenSearch client, Ollama client, PDF/image libraries, etc. The first run can take a few minutes (especially PyTorch and sentence-transformers).

**If something fails:**

- **PyTorch**: On Apple Silicon Macs you may want the MPS build; see [pytorch.org](https://pytorch.org/get-started/locally/).
- **pytesseract**: The Python package is a wrapper. For OCR you also need the **Tesseract** binary installed on your system. See [docs/PREREQUISITES.md](docs/PREREQUISITES.md).
- **OpenSearch**: You don’t need to run OpenSearch yet; `opensearch-py` is just the client. Running OpenSearch (e.g. via Docker) comes in a later step.

---

### Step 5: Confirm the main libraries

Quick sanity check:

```bash
python3 -c "
import streamlit
import sentence_transformers
import opensearchpy
import ollama
print('Streamlit:', streamlit.__version__)
print('Sentence Transformers: OK')
print('OpenSearch client: OK')
print('Ollama client: OK')
"
```

If that runs without errors, your **libraries and frameworks are installed** and you’re ready for the next steps.

---

## Next steps (after installation)

1. **Configure**  
   Edit `constants.py` (or your config) for embedding model and OpenSearch URL (e.g. `http://localhost:9200` when you run OpenSearch).

2. **Run OpenSearch** (when you’re ready)  
   Often done with Docker. See [docs/PREREQUISITES.md](docs/PREREQUISITES.md) for Docker and OpenSearch setup.

3. **Run Ollama**  
   Install from [ollama.ai](https://ollama.ai) and pull a model, e.g. `ollama pull llama3.2`. See [docs/PREREQUISITES.md](docs/PREREQUISITES.md) for details.

4. **Launch the app**  
   From the repo that contains `Welcome.py`:
   ```bash
   streamlit run Welcome.py
   ```

### Docker and switching LLM (local vs prod)

- **Local:** Run the app and Ollama in Docker: see **[docs/DOCKER.md](docs/DOCKER.md)**. Use `docker compose up` and set `LLM_PROVIDER=ollama` (default).
- **Prod:** Use OpenAI or Gemini instead of Ollama: set `LLM_PROVIDER=openai` or `LLM_PROVIDER=gemini` and the corresponding API key (e.g. `OPENAI_API_KEY`, `GEMINI_API_KEY`). No Ollama container needed. Copy `.env.example` to `.env` and fill in the keys.