# Manual download: all-mpnet-base-v2 into `embedding_model/`

If the Python download scripts fail (network, permissions, etc.), use one of these manual options.

---

## Option A: Alternative Python script (huggingface_hub)

Uses only `huggingface_hub` (no full model load in memory):

```bash
pip install huggingface_hub
python scripts/download_embedding_model_hf.py
```

Then in `src/constants.py` set:

```python
EMBEDDING_MODEL_PATH = "embedding_model"
```

---

## Option B: Git clone (requires Git + Git LFS)

1. Install [Git LFS](https://git-lfs.com/) and run once: `git lfs install`
2. From your project root:

```bash
cd /path/to/sg-local-rag-system
git clone https://huggingface.co/sentence-transformers/all-mpnet-base-v2 embedding_model
```

3. In `src/constants.py` set:

```python
EMBEDDING_MODEL_PATH = "embedding_model"
```

---

## Option C: Browser download from Hugging Face

1. Open: **https://huggingface.co/sentence-transformers/all-mpnet-base-v2/tree/main**
2. You may need to log in (free account).
3. Download the repo:
   - **“Files and versions”** tab → use **“⋮” (three dots)** or **“Download repository”** if available to get a ZIP,  
   **or**
   - Download each file listed (e.g. `config.json`, `pytorch_model.bin`, `tokenizer.json`, `tokenizer_config.json`, `vocab.txt`, `special_tokens_map.json`, and files under subfolders like `1_Pooling/` if shown).
4. Unzip (or place all files) into a folder named **`embedding_model`** at your project root, keeping the same structure as on the Hub (e.g. `embedding_model/config.json`, `embedding_model/pytorch_model.bin`, etc.).
5. In `src/constants.py` set:

```python
EMBEDDING_MODEL_PATH = "embedding_model"
```

---

## Option D: Hugging Face CLI

If you use the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli):

```bash
pip install huggingface_hub
huggingface-cli download sentence-transformers/all-mpnet-base-v2 --local-dir embedding_model
```

Then set `EMBEDDING_MODEL_PATH = "embedding_model"` in `src/constants.py`.

---

## After any option

- Ensure the folder at project root is named **`embedding_model`** and contains the model files (e.g. `config.json`, `pytorch_model.bin`, tokenizer files).
- In **`src/constants.py`**: `EMBEDDING_MODEL_PATH = "embedding_model"` and `EMBEDDING_DIMENSION = 768`.
