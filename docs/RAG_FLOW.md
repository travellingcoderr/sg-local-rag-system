# RAG Flow: How Document Upload and Search Works

This document explains what happens when you upload documents and how they're used for RAG (Retrieval-Augmented Generation).

---

## 📤 Document Upload Flow (Doc_upload.py)

When you upload a PDF document, here's what happens step-by-step:

### Step 1: Page Load (Initial Setup)
**What you see:** "RUNNING" spinner for ~1-2 minutes (first time only)

**What's happening:**
1. **Loading embedding model** (~1-2 min first time)
   - Downloads `sentence-transformers/all-mpnet-base-v2` from Hugging Face (~400MB)
   - This model converts text → vectors (embeddings) for semantic search
   - **Cached after first load** - subsequent page loads are fast

2. **Connecting to OpenSearch** (~1-2 seconds)
   - Connects to OpenSearch at `localhost:9200` (or configured host)
   - Creates the index if it doesn't exist
   - Loads list of already-indexed documents

### Step 2: Upload a PDF
**What you see:** "Uploading and processing documents..."

**What's happening:**
1. **Save file** → Saved to `uploaded_files/` directory
2. **Extract text** → PyPDF2 reads all pages and extracts text
3. **Chunk text** → Text is split into chunks of 300 characters (with 100 char overlap)
   - Example: A 1000-character document becomes ~4 chunks
   - Overlap ensures context isn't lost at chunk boundaries
4. **Generate embeddings** → Each chunk is converted to a 768-dimensional vector
   - Uses the embedding model loaded in Step 1
   - Example: `"Hello world"` → `[0.1, 0.2, ..., 0.9]` (768 numbers)
5. **Index in OpenSearch** → Each chunk is stored with:
   - `text`: The actual chunk text
   - `embedding`: The 768-dimensional vector
   - `document_name`: The filename
   - `doc_id`: Unique ID like `"document.pdf_0"`, `"document.pdf_1"`, etc.

**OpenSearch calls:**
- `get_opensearch_client()` - Gets client connection
- `create_index()` - Creates index if needed (defines fields: text, embedding, document_name)
- `bulk_index_documents()` - Stores all chunks in one batch operation

---

## 🔍 How OpenSearch Stores Your Documents

**Index structure:**
```json
{
  "documents": {
    "mappings": {
      "properties": {
        "text": { "type": "text" },           // The chunk text
        "embedding": { 
          "type": "knn_vector",
          "dimension": 768                     // Vector size
        },
        "document_name": { "type": "keyword" } // Filename
      }
    }
  }
}
```

**Example document in OpenSearch:**
```json
{
  "_id": "document.pdf_0",
  "_source": {
    "text": "This is the first chunk of text from the document...",
    "embedding": [0.1, 0.2, 0.3, ..., 0.9],  // 768 numbers
    "document_name": "document.pdf"
  }
}
```

---

## 💬 RAG Flow (When Chatbot Uses Documents)

**Note:** Currently, RAG is not fully wired into the Chatbot page. The infrastructure is ready, but the chatbot needs to be updated to:
1. Embed the user's question
2. Search OpenSearch for relevant chunks
3. Include those chunks as context in the LLM prompt

**How it would work (when implemented):**

### Step 1: User asks a question
Example: "What did the document say about X?"

### Step 2: Embed the question
- Convert user's question to a 768-dimensional vector using the same embedding model
- `"What did the document say about X?"` → `[0.3, 0.1, ..., 0.7]`

### Step 3: Hybrid search in OpenSearch
**OpenSearch call:** `hybrid_search(query_text, query_embedding, top_k=5)`

**What happens:**
- **Keyword search (BM25):** Finds chunks containing words from the question
- **Vector search (KNN):** Finds chunks with similar meaning (using cosine similarity)
- **Hybrid:** Combines both scores (30% keyword, 70% semantic)
- Returns top 5 most relevant chunks

**OpenSearch query:**
```json
{
  "query": {
    "hybrid": {
      "queries": [
        {"match": {"text": "What did the document say about X"}},  // Keyword
        {"knn": {"embedding": {"vector": [0.3, 0.1, ...], "k": 5}}}  // Vector
      ]
    }
  }
}
```

### Step 4: Build context for LLM
- Take the top 5 chunks returned from OpenSearch
- Combine them into a context string:
  ```
  Context from documents:
  [Chunk 1 text]
  [Chunk 2 text]
  ...
  
  User question: What did the document say about X?
  ```

### Step 5: Send to LLM
- Send the context + question to Ollama/OpenAI/Gemini
- LLM generates answer using both:
  - Its training knowledge
  - The specific context from your documents

---

## 📊 Complete Flow Diagram

```
┌─────────────────┐
│  Upload PDF     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Text     │ (PyPDF2)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Chunk Text       │ (300 chars, 100 overlap)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate         │ (Embedding model)
│ Embeddings       │ (Text → 768-dim vector)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Store in         │ (OpenSearch bulk_index)
│ OpenSearch       │
└─────────────────┘

[Later, when user asks question]

┌─────────────────┐
│ User Question    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Embed Question   │ (Same embedding model)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Hybrid Search    │ (OpenSearch)
│ in OpenSearch    │ (Keyword + Vector)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get Top Chunks   │ (Top 5 relevant chunks)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build Prompt     │ (Context + Question)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Send to LLM      │ (Ollama/OpenAI/Gemini)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Answer    │
└─────────────────┘
```

---

## 🔧 Key Files and Functions

| File | Function | What it does |
|------|----------|--------------|
| `pages/2_Doc_upload.py` | `render_upload_page()` | Main upload page logic |
| `src/embeddings.py` | `get_embedding_model()` | Loads embedding model |
| `src/embeddings.py` | `generate_embeddings()` | Converts text chunks → vectors |
| `src/utils.py` | `chunk_text_by_characters()` | Splits text into chunks |
| `src/opensearch.py` | `get_opensearch_client()` | Creates OpenSearch connection |
| `src/ingestion.py` | `create_index()` | Creates OpenSearch index |
| `src/ingestion.py` | `bulk_index_documents()` | Stores chunks in OpenSearch |
| `src/opensearch.py` | `hybrid_search()` | Searches for relevant chunks (for RAG) |

---

## ⚡ Performance Notes

**First-time page load (2 minutes):**
- Downloading embedding model from Hugging Face (~400MB)
- Happens once, then cached

**Subsequent page loads:**
- Fast (~1-2 seconds) - model is cached

**Uploading a document:**
- Small PDF (< 10 pages): ~5-10 seconds
- Large PDF (50+ pages): ~30-60 seconds
- Depends on: document size, number of chunks, embedding generation time

**To speed up:**
- Pre-download embedding model: `python scripts/download_embedding_model_hf.py`
- Set `EMBEDDING_MODEL_PATH=embedding_model` in `.env`
- This avoids the Hugging Face download on first load

---

## 🎯 Your Understanding is Correct!

You correctly understood:
- ✅ Documents are uploaded and text is extracted
- ✅ Text is chunked into smaller pieces
- ✅ Chunks are stored in OpenSearch with embeddings
- ✅ When a prompt happens, relevant chunks are retrieved and used as context for the LLM

The only missing piece is wiring RAG into the Chatbot page (currently the chatbot doesn't use the documents yet, but all the infrastructure is ready).
