# Python learnings

This file is updated whenever you ask Python-related technical questions. Treat it as a running reference from our conversations.

---

## `__init__.py` and package structure

**Why do we need `src/__init__.py`?**

In Python, a folder is only treated as an **importable package** if it contains an `__init__.py` file.

- **With `src/__init__.py`:** `src` is a package → you can do `from src.constants import ...` or `import src.constants`.
- **Without it:** `src` is just a folder and those imports fail (unless you mess with `PYTHONPATH`).

So `__init__.py` doesn’t “start” the app—it **marks the folder as a package** so other code can import from it. The file can be empty; that’s normal.

---

## Entry point of a Python project

Unlike C#, Python has **no single mandatory entry point**. The “starting point” is **whatever file you run**.

| How you run | What is the starting point |
|-------------|----------------------------|
| `python some_script.py` | `some_script.py` |
| `streamlit run Welcome.py` | `Welcome.py` |
| `python -m mypackage` | `mypackage/__main__.py` (if it exists) |

In this RAG project, the starting point is **`Welcome.py`** (run with `streamlit run Welcome.py`). `src/__init__.py` is not the entry point; it only enables `import src....`

---

## Streamlit: creating and running a web app (vs ASP.NET)

**Coming from C# ASP.NET:** In ASP.NET you have a project, a web server (Kestrel/IIS), controllers, views, and you “run” the project to start the server. In Streamlit there is no separate server project or config—**one Python script is the app**. You run that script with `streamlit run`, and Streamlit starts a local server and opens the UI in the browser.

### What files you need (minimum)

| Need | In ASP.NET world | In Streamlit |
|------|------------------|--------------|
| Entry point | Program.cs / Startup / host | **One .py file** (e.g. `Welcome.py`) |
| UI | Razor views, HTML, JS | **Same .py file** – you call `st.title()`, `st.button()`, etc. in Python |
| Run command | `dotnet run` or F5 | `streamlit run Welcome.py` |

So to “create the Streamlit app from scratch” you only need:

1. **One Python file** (e.g. `Welcome.py`) at the project root (or anywhere).
2. In that file: `import streamlit as st` and then use `st.*` to build the page (title, inputs, buttons, etc.).
3. **Run it:** from the folder that contains `Welcome.py`, with your venv activated:
   ```bash
   streamlit run Welcome.py
   ```
   Streamlit will start, print a local URL (e.g. http://localhost:8501), and often open the browser. That URL is your “browser app.”

No separate HTML/CSS/JS files, no routing config, no `Program.cs`—just the one script.

### How to run it

1. Activate your virtual environment (e.g. `source .venv/bin/activate`).
2. From the **project root** (where `Welcome.py` lives):
   ```bash
   streamlit run Welcome.py
   ```
3. Open the URL shown in the terminal (usually http://localhost:8501). That’s the app.

So: **same idea as “running the ASP.NET app”** (start the process, open browser to the app URL), but the “project” is just this one script and the run command is `streamlit run <that_script>.py`.

### How Streamlit behaves (mental model)

- Your script runs **top to bottom**.
- When the user interacts (click, type, etc.), Streamlit **re-runs the script** and redraws the page from the current state. You don’t write event handlers like in WinForms/WPF; you write the full page in one script and Streamlit re-executes it on each interaction.
- Widgets like `st.text_input()` and `st.button()` both **show** the control and **return** its value; you use that return value in Python to decide what to show next (e.g. “if name: st.success(...)”).

### In this repo

- **File that is the app:** `Welcome.py` (at the project root).
- **How to run:** `streamlit run Welcome.py` from the project root, with venv activated.
- **Dependency:** `streamlit` must be installed (`pip install -r requirements.txt` already includes it).

---

## Streamlit multi-page apps: automatic sidebar navigation

**How the sidebar links ("Welcome", "Chatbot", "Upload Documents") are created:**

Streamlit has an **automatic multi-page app** feature. When you run `streamlit run Welcome.py`, Streamlit:

1. **Looks for a `pages/` folder** in the same directory as `Welcome.py`.
2. **Automatically creates navigation links** in the sidebar for each `.py` file it finds in `pages/`.
3. **The main file (`Welcome.py`) becomes the home page** (shown as "welcome" or the filename).

### How it works

| File structure | What shows in sidebar |
|----------------|----------------------|
| `Welcome.py` (at root) | "welcome" (home page) |
| `pages/1_🤖_Chatbot.py` | "🤖 Chatbot" |
| `pages/2_📄_Upload_Documents.py` | "📄 Upload Documents" |

### Naming conventions

- **Numbers prefix (`1_`, `2_`)**: Control the **order** of links in the sidebar (1 comes before 2).
- **Emojis**: Show up in the link text (e.g., `1_🤖_Chatbot.py` → "🤖 Chatbot").
- **Underscores**: Converted to spaces in the link text (`Upload_Documents` → "Upload Documents").
- **No manual navigation code needed**: You don’t write `st.sidebar.link()` or routing—Streamlit does it automatically.

### In `Welcome.py`

**You don’t manually create the navigation links.** `Welcome.py` only:
- Sets page config (`st.set_page_config()`)
- Adds custom CSS
- Displays sidebar content (logo, footer, etc.) using `st.sidebar.*`
- Displays main page content

The **navigation links are added automatically** by Streamlit when it detects the `pages/` folder.

### Example structure

```
sg-local-rag-system/
  Welcome.py              ← Main/home page (shows as "welcome")
  pages/
    1_🤖_Chatbot.py       ← Shows as "🤖 Chatbot" in sidebar
    2_📄_Upload_Documents.py  ← Shows as "📄 Upload Documents" in sidebar
```

**C# ASP.NET analogy:** Like having a `Controllers/` folder where each controller automatically gets a route—except Streamlit does it for you just by having files in `pages/`. No routing config needed.

---

## How the prompt gets to the LLM and the response comes back (Chatbot)

**Data flow in this app (baby-step version, no RAG yet):**

1. **UI**  
   You type in `st.chat_input("...")`. Streamlit gives that text as the variable `prompt`.

2. **Session state**  
   We append `{"role": "user", "content": prompt}` to `st.session_state["chat_history"]` so we can show history and send it to the LLM.

3. **Building the request**  
   In `src/chat.py`, `generate_response_streaming(prompt, chat_history, temperature)`:
   - Builds a **messages** list: previous user/assistant turns from `chat_history` (e.g. last 10 turns) plus the new user message.
   - That list is what the LLM expects: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]`.

4. **Sending to the LLM**  
   We call **`ollama.chat(model=OLLAMA_MODEL_NAME, messages=messages, stream=True, options={"temperature": temperature})`**.  
   The Ollama library sends an HTTP request to your local Ollama server (e.g. `http://localhost:11434`). The server runs the model (e.g. `llama3.2:1b`) and starts streaming the reply.

5. **Receiving the response**  
   Because `stream=True`, `ollama.chat()` returns a **generator** that yields **chunks**. Each chunk is a piece of the assistant’s reply (often a few tokens). In this app we use `chunk["message"]["content"]` (or the same as object attributes) to get the text.

6. **Display**  
   The Chatbot page loops over the stream, concatenates each chunk into `response_text`, and updates `response_placeholder.markdown(response_text + "▌")` so the user sees the reply appear token-by-token. When the stream ends, we append `{"role": "assistant", "content": response_text}` to `chat_history`.

**In one line:**  
`prompt` → `messages` list → `ollama.chat(messages=..., stream=True)` → HTTP to local Ollama → model generates → stream of chunks → we concatenate and show in the UI.

**Files involved:**  
- **`pages/1_Chatbot.py`**: UI, `st.chat_input`, `st.chat_message`, calls `generate_response_streaming`, displays stream.  
- **`src/chat.py`**: `_build_messages()`, `generate_response_streaming()`, `ollama.chat()`.  
- **`src/constants.py`**: `OLLAMA_MODEL_NAME` (which model to call).

---

## Two kinds of models: embeddings vs LLM (understanding the stack)

From an understanding point of view the stack has two parts:

1. **Embedding models (e.g. Hugging Face / sentence-transformers)**  
   - **Role:** Turn **text** into **vectors** (embeddings) for **semantic similarity**.  
   - **Used for:** Storing and searching your documents (e.g. in OpenSearch). When you index a doc, you embed each chunk; when the user asks a question, you embed the question and search for chunks whose embeddings are close.  
   - **Input:** text → **Output:** list of numbers (embedding).  
   - **Not** used as the direct input to the LLM.

2. **LLM (e.g. Ollama, local)**  
   - **Role:** Take **text** in, generate **text** out (chat, answers).  
   - **Input:** **text** prompts (and optionally conversation history).  
   - **Output:** text response (streamed or full).  
   - The LLM does **not** receive embedding vectors—only natural language.

**Important:** The LLM gets **text** prompts, not “embedding prompts.” Embeddings are used for **retrieval** (finding which document chunks are relevant). When you add RAG: you use embeddings to **find** the relevant chunks, then you pass the **text** of those chunks (plus the user question) as the **text** prompt to the LLM. So: embeddings → help choose what text to show the LLM; the LLM only ever sees text.

| Component | Input | Output | Purpose |
|-----------|--------|--------|---------|
| Sentence-transformers (embedding model) | Text (e.g. doc chunk, user query) | Vector (list of floats) | Semantic search / retrieval |
| Ollama (LLM) | Text (prompt + optional context) | Text (reply) | Generate the answer |

---

## How OpenSearch is used in this RAG app

OpenSearch is the **search backend** where we store document chunks and their embeddings, and where we run **hybrid search** (keyword + semantic) to find relevant chunks for RAG.

### What OpenSearch is

- **OpenSearch** is an open-source search engine (fork of Elasticsearch). It stores **documents** in **indices** and lets you search by **keywords** (like a classic search engine) and by **vectors** (similarity search).
- In this project we run it **locally** (e.g. in Docker). The app talks to it over HTTP at `OPENSEARCH_HOST:OPENSEARCH_PORT` (e.g. `localhost:9200`).
- We use it as a **vector store**: each “document” in the index is one **text chunk** plus its **embedding** and the **source file name**.

### Why we use it here

1. **Store** – When you upload a PDF on the **Upload Documents** page, we split the text into chunks, turn each chunk into an embedding, and **index** them in OpenSearch (text + embedding + document name).
2. **Search** – When you ask a question in the **Chatbot** with RAG on, we embed your question, run **hybrid search** in OpenSearch (keyword match + vector similarity), and get back the most relevant **chunks** (as text). That text is then passed to the LLM as context.

So: **OpenSearch = the place where “your documents” live as searchable chunks and vectors.** The LLM never talks to OpenSearch; the app does, and then gives the LLM the retrieved text.

### What gets stored in OpenSearch (the index)

We have **one index** (name in `OPENSEARCH_INDEX`, e.g. `"documents"`). Each **document** in that index represents **one chunk** of a PDF and has:

| Field | Type | Meaning |
|-------|------|--------|
| **`text`** | text | The chunk’s raw text (searchable by keywords). |
| **`embedding`** | knn_vector | The chunk’s embedding (list of floats, e.g. 768). Used for similarity search. |
| **`document_name`** | keyword | The source file name (e.g. `"report.pdf"`). Used to list or delete “all chunks of this file”. |

The **index mapping** (field types, vector dimension) is defined in **`src/index_config.json`** and applied when we **create** the index. The app sets the vector **dimension** from `EMBEDDING_DIMENSION` in constants so it matches the embedding model.

### Two ways the app uses OpenSearch

**1. Upload / ingestion (Doc upload page)**  
- **Create index** – `create_index(client)` so the index exists with the right mapping (text, knn_vector, document_name).  
- **Bulk index** – For each uploaded PDF we build a list of “documents” (one per chunk: `doc_id`, `text`, `embedding`, `document_name`) and call **`bulk_index_documents(documents)`**. That sends them to OpenSearch in one bulk request.  
- **Delete** – When you delete a file, we call **`delete_documents_by_document_name(document_name)`**, which runs a delete-by-query so all chunks of that file are removed from the index.  
- **List** – We run an **aggregation** on `document_name` to get the list of “which files are in the index” and show them on the page.

**2. Search / RAG (Chatbot when RAG is enabled)**  
- We take the user’s **query text**, embed it with the same model we used for chunks → **query_embedding**.  
- We call **`hybrid_search(query_text, query_embedding, top_k)`**.  
- OpenSearch runs **two** searches and combines them:  
  - **Keyword (BM25)** – `match` on the `text` field (classic full-text search).  
  - **Vector (KNN)** – find chunks whose `embedding` is closest to `query_embedding`.  
- The **search pipeline** `nlp-search-pipeline` (set up in PREREQUISITES) normalizes and merges the two scores so we get one ranked list.  
- We get back the **top_k** chunks (without the `embedding` field to save bandwidth). Those chunks’ **text** is then passed to the LLM as context.

### Hybrid search in one picture

```
User question: "What did the report say about costs?"
        │
        ▼
Embed question → query_embedding (e.g. 768 floats)
        │
        ▼
OpenSearch: hybrid_search(query_text, query_embedding, top_k=5)
        │
        ├── BM25:  match "text" with "What did the report say about costs?"
        ├── KNN:   nearest neighbors of query_embedding in "embedding" field
        └── Pipeline: combine scores → return top 5 chunks (text only)
        │
        ▼
App: take those 5 chunks’ text → build prompt: "Context: ... User: ..." → send to LLM
```

### Where it lives in the code

| What | Where |
|------|--------|
| **Connect to OpenSearch** | `src/opensearch.py` → `get_opensearch_client()` (uses `OPENSEARCH_HOST`, `OPENSEARCH_PORT`). |
| **Index config (mapping)** | `src/index_config.json`; dimension overridden in `src/ingestion.py` → `load_index_config()`. |
| **Create index** | `src/ingestion.py` → `create_index(client)`. |
| **Bulk index / delete by doc name** | `src/ingestion.py` → `bulk_index_documents()`, `delete_documents_by_document_name()`. |
| **Hybrid search** | `src/opensearch.py` → `hybrid_search(query_text, query_embedding, top_k)` (uses `search_pipeline="nlp-search-pipeline"`). |
| **Upload page** | `pages/2_Doc_upload.py` – calls ingestion + embeddings; lists docs via OpenSearch aggregation. |
| **Chatbot with RAG** | When RAG is wired in, the chat flow would call `get_embedding_model()`, encode the query, then `hybrid_search()`, then build the prompt with the returned chunks and send to the LLM. |

### Summary

- **OpenSearch** = search engine running locally; we use it as the **store** for document chunks and their embeddings, and for **hybrid** (keyword + vector) search.  
- **Index** = one place (e.g. `documents`) where each “row” is a chunk with `text`, `embedding`, `document_name`.  
- **Ingestion** = create index + bulk index chunks (and delete by document name).  
- **Retrieval** = embed the user question, run hybrid search, get back chunk **text**, feed that text to the LLM as context.  
- The **LLM** only sees text; it never talks to OpenSearch. The app is the one that reads/writes OpenSearch and then builds the prompt for the LLM.

---

## Project files: `app.log`, `mypy.ini`, `pyproject.toml`, and the `logs/` folder

### `app.log` (at project root)

- **What it is:** A **log file** produced when the application runs. It’s the same kind of output as `logs/app.log` (see below).
- **Why it exists in the reference repo:** Either from an older config that wrote to `app.log` at the root, or a run that used that path. Many projects ignore `*.log` in `.gitignore` so these files aren’t committed; if you see `app.log` in a repo, it’s usually generated at runtime and could be left out of version control.
- **In our repo:** We configure logging to write to **`logs/app.log`** in `src/constants.py` (`LOG_FILE_PATH`). We don’t need a root `app.log` unless you add a second logger that targets it.

### `logs/` folder and how logs get into it

- **What it is:** A directory where the app writes its log file (e.g. `logs/app.log`).
- **How logs get there:**  
  1. **Config:** In `src/constants.py`, `LOG_FILE_PATH = "logs/app.log"`.  
  2. **Setup:** Somewhere early in the app (e.g. in `src/utils.py`) a **logging** setup function runs: it reads `LOG_FILE_PATH` and calls Python’s `logging.basicConfig(filename=LOG_FILE_PATH, filemode="a", ...)`. That tells the standard `logging` library: “send log records to this file.”  
  3. **Writing:** Any module that does `logger = logging.getLogger(__name__)` and then `logger.info("...")` (or `logger.error(...)`, etc.) will write to that file. The path is relative to the **current working directory** when you run the app (usually the project root), so `logs/app.log` means “file `app.log` inside the `logs/` folder.”  
- **Summary:** The app doesn’t “copy” logs into the folder; the **Python `logging` module** is configured once with `LOG_FILE_PATH`, and every `logger.info()` (etc.) appends to that file. Create the `logs/` folder if it doesn’t exist, or ensure the code creates it before opening the file, so the first run doesn’t fail.

### `mypy.ini`

- **What it is:** Configuration for **mypy**, a static type checker for Python (like running extra compile-time checks on types).
- **Why it exists:** So that when you run `mypy .` (or `mypy src/`), mypy knows how to behave: which files to check, strictness, Python version, etc. The reference repo uses it to keep type hints consistent.
- **Do you need it?** Only if you want to run mypy. It’s optional and doesn’t affect running the app. No mypy = no `mypy.ini` needed.

### `pyproject.toml`

- **What it is:** The standard place for **Python project metadata and tool configuration** (PEP 518). Think of it as a mix of “project settings” and “tool preferences” in one file.
- **What’s in it (in the reference repo):** Only **tool config**, e.g. for **Black** (code formatter) and **isort** (import sorter): line length, quote style, etc. So `pyproject.toml` is not used to install dependencies there (they use `requirements.txt` for that); it’s used so that when you run `black .` or `isort .`, those tools read their options from this file.
- **C# analogy:** Roughly like having a shared EditorConfig or some analyzer/formatting settings that the IDE and CLI tools respect. The project still “runs” without it; it’s for code style and tooling.
- **Do you need it?** Only if you use Black, isort, or other tools that read from `pyproject.toml`. Optional for running the app.
