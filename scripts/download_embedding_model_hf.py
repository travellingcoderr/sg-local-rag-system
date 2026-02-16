"""
Alternative: download all-mpnet-base-v2 using huggingface_hub (no SentenceTransformer load).
Run: pip install huggingface_hub
Then: python scripts/download_embedding_model_hf.py
"""
from pathlib import Path

REPO_ID = "sentence-transformers/all-mpnet-base-v2"
SAVE_DIR = Path(__file__).resolve().parent.parent / "embedding_model"


def main() -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Install huggingface_hub: pip install huggingface_hub")
        raise

    print(f"Downloading {REPO_ID} to {SAVE_DIR}...")
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=REPO_ID, local_dir=str(SAVE_DIR))
    print(f"Done. Set EMBEDDING_MODEL_PATH = 'embedding_model' in src/constants.py")


if __name__ == "__main__":
    main()
