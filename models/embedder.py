import numpy as np
import torch
from sentence_transformers import SentenceTransformer

_model = None


def get_embedder():
    global _model
    if _model is None:
        print("Loading embedder on GPU...")
        _model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2',
            device="cuda"
        )
        print("Embedder loaded ✓")
    return _model


def embed_chunks(chunks: list) -> np.ndarray:
    """
    Takes a list of chunk dicts and returns embeddings as numpy array.
    """
    model = get_embedder()
    texts = [c['text'] for c in chunks]
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    return embeddings


def embed_text(text: str) -> np.ndarray:
    """Embed a single string — used for similarity search queries."""
    model = get_embedder()
    return model.encode(text, convert_to_numpy=True)


def embedding_to_bytes(embedding: np.ndarray) -> bytes:
    """Convert embedding to bytes for SQLite storage."""
    return embedding.astype(np.float32).tobytes()


def bytes_to_embedding(b: bytes) -> np.ndarray:
    """Convert bytes from SQLite back to numpy array."""
    return np.frombuffer(b, dtype=np.float32)


def free_embedder():
    """Free GPU memory after embedding is done."""
    global _model
    _model = None
    torch.cuda.empty_cache()
    print("Embedder freed from GPU ✓")