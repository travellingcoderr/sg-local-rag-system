# Installing prerequisites

This document walks you through installing **everything required to run the local RAG app**: Python, Docker, Ollama, OpenSearch (and Dashboard), the hybrid search pipeline, Python dependencies, and configuration. Follow the sections in order.

---

## 1. Python 3.10 or newer

The project requires Python 3.10+ (3.11 is a good choice).

### Check if you already have it

```bash
python3 --version
# or
python --version
```

You should see something like `Python 3.10.x` or `Python 3.11.x`.

### Install if needed

- **macOS**  
  - Option A: Install from [python.org](https://www.python.org/downloads/) (macOS installer).  
  - Option B: With Homebrew: `brew install python@3.12`
- **Windows**  
  Download the installer from [python.org](https://www.python.org/downloads/). During setup, enable **“Add Python to PATH”**.
- **Linux (Debian/Ubuntu)**  
  `sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip`
- **Linux (Fedora)**  
  `sudo dnf install python3.11 python3-pip`

Verify again with `python3 --version` (or `python --version` on Windows).

---

## 2. pip (Python package installer)

pip usually comes with Python. Check:

```bash
pip3 --version
# or
pip --version
```

### Install or upgrade pip

If it’s missing or very old:

```bash
python3 -m ensurepip --upgrade
# or
python3 -m pip install --upgrade pip
```

On Linux you may need: `sudo apt install python3-pip` (Debian/Ubuntu) or `sudo dnf install python3-pip` (Fedora).

---

## 3. Virtual environment (venv)

Using a virtual environment keeps this project’s dependencies separate from the rest of your system. No extra install is needed: venv is included in Python 3.3+.

From the project root:

```bash
# Create
python3 -m venv .venv

# Activate
# macOS / Linux:
source .venv/bin/activate
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

Your prompt should show `(.venv)`. Use this venv for all following `pip` commands.

---

## 4. Docker

Docker is required to run OpenSearch locally. It gives you an isolated environment for storing, indexing, and retrieving document embeddings.

### Install Docker

- **macOS / Windows**  
  Install [Docker Desktop](https://docs.docker.com/get-docker/) and start it.
- **Linux**  
  Follow the official [Docker Engine install](https://docs.docker.com/engine/install/) for your distro.

### Confirm Docker is running

```bash
docker --version
```

If you see a version number, Docker is installed. Ensure Docker Desktop (or the Docker daemon) is running before the next steps. You can run this command to see any processes in docker.

```bash
docker ps
```

---

## 5. Ollama

Ollama runs the local LLM that answers questions using your retrieved documents. It runs fully on your machine without the cloud.

### Install Ollama

Download and install from [ollama.ai](https://ollama.ai) for your OS.

### Confirm installation

```bash
ollama --version
```

### (Optional) Test with a model

To confirm everything works, run a small model and chat briefly:

```bash
ollama run llama3.2:1b
```

Type a short message and press Enter. Type `/bye` or exit the process when done. You can also try other models from the [Ollama library](https://ollama.ai/library); for the RAG app you’ll configure the model name in `constants.py` (e.g. `llama3.2:1b` or `llama3.2`).

---

## 6. OpenSearch and OpenSearch Dashboard

OpenSearch is the vector store where document embeddings are indexed; the Dashboard gives you a web UI to inspect indices and run queries.

### Pull the Docker images

Use OpenSearch 2.11 and the matching Dashboard:

```bash
# OpenSearch 2.11
docker pull opensearchproject/opensearch:2.11.0

# OpenSearch Dashboard 2.11
docker pull opensearchproject/opensearch-dashboards:2.11.0
```

### Run the OpenSearch container

Start OpenSearch in single-node mode with security disabled for local use:

```bash
docker run -d --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:2.11.0
```

- **Port 9200**: REST API (used by the app).
- **Port 9600**: Performance analyzer (optional).

### Verify

1. Open [http://localhost:9200](http://localhost:9200) in your browser. You should see the OpenSearch Running.

### Run the OpenSearch Dashboard container

Start the Dashboard and link it to the OpenSearch container:

```bash
docker run -d --name opensearch-dashboards \
  -p 5601:5601 \
  --link opensearch:opensearch \
  -e "OPENSEARCH_HOSTS=http://opensearch:9200" \
  -e "DISABLE_SECURITY_DASHBOARDS_PLUGIN=true" \
  opensearchproject/opensearch-dashboards:2.11.0
```

### Verify

1. Open [http://localhost:5601](http://localhost:5601) in your browser. You should see the OpenSearch Dashboard.
2. If the Dashboard loads, OpenSearch is running and the app can use `http://localhost:9200` to talk to it.

To stop the containers later:

```bash
docker stop opensearch-dashboards opensearch
docker rm opensearch-dashboards opensearch
```

---

## 7. Enable hybrid search in OpenSearch

Hybrid search combines keyword search (BM25) with vector (semantic) search. The app uses a search pipeline that normalizes and combines both scores.

### Create the search pipeline

Run this in your terminal (with OpenSearch running):

```bash
curl -XPUT "http://localhost:9200/_search/pipeline/nlp-search-pipeline" -H 'Content-Type: application/json' -d'
{
  "description": "Post processor for hybrid search",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": {
          "technique": "min_max"
        },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": {
            "weights": [0.3, 0.7]
          }
        }
      }
    }
  ]
}
'
```

You should get a JSON response with `"acknowledged": true`.

### Alternative: create via OpenSearch Dashboard

1. Open [http://localhost:5601](http://localhost:5601).
2. Go to **Dev Tools**.
3. Paste and run:

```json
PUT /_search/pipeline/nlp-search-pipeline
{
  "description": "Post processor for hybrid search",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": {
          "technique": "min_max"
        },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": {
            "weights": [0.3, 0.7]
          }
        }
      }
    }
  ]
}
```

The pipeline is now set. The app will use it when performing hybrid search (e.g. 0.3 weight for BM25, 0.7 for vector search; you can change these in the JSON if needed).

---

## 8. Tesseract OCR (optional)

Only needed if you want to extract text from **images** or **scanned PDFs**. The Python package `pytesseract` is a wrapper; the Tesseract binary must be installed on your system.

### Install Tesseract

- **macOS (Homebrew)**  
  `brew install tesseract`
- **Windows**  
  Use the installer from [GitHub – tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki) and add its install directory to your system PATH.
- **Linux (Debian/Ubuntu)**  
  `sudo apt install tesseract-ocr`
- **Linux (Fedora)**  
  `sudo dnf install tesseract`

Check:

```bash
tesseract --version
```

You can skip this and still run the app; OCR is only used when you process image-based or scanned documents.

---

## 9. Install Python dependencies

With your virtual environment **activated** and from the project root (where `requirements.txt` is):

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs Streamlit, sentence-transformers, PyTorch, opensearch-py, ollama, PyPDF2, pytesseract, Pillow, and the rest. The first run can take several minutes (especially PyTorch and sentence-transformers).

### If something fails

- **PyTorch**  
  On Apple Silicon Macs you may need a specific build; see [pytorch.org](https://pytorch.org/get-started/locally/).
- **pytesseract**  
  Install the Tesseract binary (section 8) if you need OCR; otherwise the app can still run for text-only PDFs.
- **opensearch-py**  
  This is only the client library. OpenSearch itself runs in Docker (section 6).

### Sanity check

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

If this runs without errors, dependencies are installed correctly.

---

## 10. Configure the application

The app reads settings from **`src/constants.py`**. This file already exists in the project; you only need to edit it if you want to change defaults.

### Where the file lives

```
sg-local-rag-system/
  src/
    constants.py   <-- edit this file
```

### What each variable does

| Variable | What it controls | Default | When to change |
|----------|------------------|---------|----------------|
| **EMBEDDING_MODEL_PATH** | Which model turns text into vectors for semantic search. | `"sentence-transformers/all-mpnet-base-v2"` | Use a local folder path (e.g. `"embedding_model/"`) if you pre-downloaded a model for faster startup. |
| **ASSYMETRIC_EMBEDDING** | Whether the model uses different encodings for queries vs documents. | `False` | Leave `False` for standard Sentence Transformer models. |
| **EMBEDDING_DIMENSION** | Size of each embedding vector. Must match the model. | `768` | Change to `384` if you use e.g. `all-MiniLM-L6-v2` or `all-MiniLM-L12-v2`. |
| **TEXT_CHUNK_SIZE** | Max characters per chunk when splitting documents. | `300` | Smaller = more precise retrieval, more chunks. Larger = more context per chunk. Tune to your docs. |
| **OLLAMA_MODEL_NAME** | Which Ollama model answers chat questions. | `"llama3.2:1b"` | Set to any model you pulled (e.g. `"llama3.2"`, `"mistral"`, `"phi"`). Must match `ollama list`. |
| **LOG_FILE_PATH** | Where the app writes its log file. | `"logs/app.log"` | Change only if you want logs elsewhere. |
| **OPENSEARCH_HOST** | Hostname of your OpenSearch server. | `"localhost"` | Use `"localhost"` when OpenSearch runs in Docker on this machine (step 6). |
| **OPENSEARCH_PORT** | OpenSearch HTTP port. | `9200` | Change only if you run OpenSearch on a different port. |
| **OPENSEARCH_INDEX** | Name of the index that stores document chunks. | `"documents"` | Usually leave as-is; change only to separate different projects. |

### Embedding model options

- **Option A (faster startup):** Download a model (e.g. `sentence-transformers/all-mpnet-base-v2`) once and save it in a folder such as `embedding_model/`. Set `EMBEDDING_MODEL_PATH` to that folder path (e.g. `"embedding_model/"`).
- **Option B (default):** Keep `EMBEDDING_MODEL_PATH` as the Hugging Face model name. The app will download it on first run.

Always set **EMBEDDING_DIMENSION** to match your model: `768` for all-mpnet-base-v2, `384` for all-MiniLM-L6-v2 / all-MiniLM-L12-v2.

### Do I need to create constants.py?

No. The project already includes **`src/constants.py`** with the variables above. Open it and adjust any value (e.g. `OLLAMA_MODEL_NAME` or `EMBEDDING_MODEL_PATH`) to match your setup; the defaults work with the Docker OpenSearch setup from step 6 and a typical Ollama install.

---

## 11. Launch the application

1. Ensure **OpenSearch** (and optionally OpenSearch Dashboard) containers are running (section 6).
2. Ensure **Ollama** is installed and you have pulled a model (section 5).
3. With your **venv activated** and from the project root (where the app entrypoint lives, e.g. `Welcome.py`):

```bash
streamlit run Welcome.py
```

4. Open your browser to [http://localhost:8501](http://localhost:8501).

The first time, the app may load or download the embedding model; wait until the UI is ready. Then you can upload documents and use the chatbot with RAG (retrieval-augmented generation) enabled.

---

## Quick checklist

| Step | What | How to check |
|------|------|----------------|
| 1 | Python 3.10+ | `python3 --version` |
| 2 | pip | `pip3 --version` |
| 3 | Virtual environment | Created and activated (prompt shows `(.venv)`) |
| 4 | Docker | `docker --version`; daemon running |
| 5 | Ollama + model | `ollama --version`; `ollama list` |
| 6 | OpenSearch + Dashboard | Containers running; [http://localhost:5601](http://localhost:5601) loads |
| 7 | Hybrid search pipeline | `curl` or Dev Tools pipeline created |
| 8 | Tesseract (optional) | `tesseract --version` |
| 9 | Python deps | `pip install -r requirements.txt`; sanity check script runs |
| 10 | Config | `constants.py` (or equivalent) set with model path, dimensions, Ollama model, OpenSearch URL |
| 11 | Run app | `streamlit run Welcome.py` → [http://localhost:8501](http://localhost:8501) |

Once all steps are done, you have everything required to run the app end to end. For day-to-day usage, see [README.md](README.md) for project overview and quick commands.

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run welcome.py
