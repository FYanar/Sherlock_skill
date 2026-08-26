"""
Embedding engine for the Sherlock Knowledge Base.
Generates normalized float32 dense vector embeddings using a lightweight,
deterministic TF-IDF / Subword Hashing vector space encoder.

IMPORTANT — hash() non-determinism fix:
Python's built-in hash() uses PYTHONHASHSEED randomization — the same string
returns different values across Python processes. This breaks persistent
cosine/vector similarity (vectors stored in SQLite become incompatible with
query vectors from a new process). We use hashlib.md5 instead, which is
fully deterministic across processes, platforms, and Python versions.
"""

import hashlib
import math
import re
import numpy as np
from typing import List

EMBEDDING_DIM = 256


def _stable_hash(s: str, dim: int) -> int:
    """Deterministic hash using MD5 — consistent across all Python processes."""
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % dim


class EmbeddingEngine:
    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        raw_tokens = re.findall(r'[a-z0-9_]+', text)
        tokens = []
        for tok in raw_tokens:
            subparts = tok.split('_')
            tokens.extend([p for p in subparts if len(p) > 1])
            tokens.append(tok)
        return tokens

    def embed_text(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return np.zeros(self.dim, dtype=np.float32)

        tokens = self._tokenize(text)
        if not tokens:
            return np.zeros(self.dim, dtype=np.float32)

        vec = np.zeros(self.dim, dtype=np.float32)

        for idx, token in enumerate(tokens):
            pos_weight = 1.0 + 0.1 * math.exp(-idx / 50.0)
            h1 = _stable_hash(token, self.dim)
            vec[h1] += 1.5 * pos_weight

            for i in range(len(token) - 1):
                bigram = token[i:i+2]
                h2 = _stable_hash(bigram, self.dim)
                vec[h2] += 0.5 * pos_weight

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.astype(np.float32)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        return [self.embed_text(t) for t in texts]
