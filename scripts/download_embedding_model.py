"""
Download sentence-transformers/all-mpnet-base-v2 to the local embedding_model/ folder.
Run once with: python scripts/download_embedding_model.py
Then set EMBEDDING_MODEL_PATH = "embedding_model" in src/constants.py for faster startup.
"""
from pathlib import Path

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
SAVE_DIR = Path(__file__).resolve().parent.parent / "embedding_model"


def main() -> None:
    print(f"Downloading {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(SAVE_DIR))
    print(f"Saved to {SAVE_DIR}")


if __name__ == "__main__":
    main()
