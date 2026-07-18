"""Replaceable embedding interface; production semantic provider."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import unicodedata
from pathlib import Path
from typing import List, Protocol, Set


STOPWORDS = {
    "la", "va", "cua", "cho", "co", "mot", "cac", "de", "duoc", "doanh", "nghiep",
    # Purely grammatical/functional words -- expanded after observing that a small
    # stopword list let unrelated queries (dog training, anime, cooking) reach the
    # sparse>=0.2 grounding gate once the corpus grew past ~150 chunks (any short
    # generic word matched something). Diacritic-fold homonyms (e.g. "quán" shop vs
    # "quản" manage both fold to "quan") are NOT fixable here and remain a known
    # limitation of this deterministic bag-of-words fallback, not a bug.
    "trong", "ngoai", "tren", "duoi", "giua", "ve", "voi", "tu", "den", "nhu",
    "ra", "vao", "sau", "truoc", "nay", "kia", "ay", "nao", "gi", "ai", "sao",
    "the", "nen", "boi", "tai", "khi", "neu", "hay", "toi", "ta",
}


def fold(text: str) -> str:
    value = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn").replace("đ", "d")


def tokens(text: str) -> Set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9-]+", fold(text))
        if len(token) > 1 and token not in STOPWORDS
    }


def cosine(left: List[float], right: List[float]) -> float:
    return max(0.0, sum(a * b for a, b in zip(left, right)))


class EmbeddingProvider(Protocol):
    name: str
    dimension: int

    def embed(self, text: str) -> List[float]: ...


class CachedGeminiEmbedding:
    """Production embedding provider via Google AI Studio (``google-genai`` SDK).

    Uses the AI Studio key (``GOOGLE_API_KEY``) and ``gemini-embedding-2`` by
    default, with a local cache so repeated calls are offline and CI is
    deterministic after a warm cache. Falls back to ``openai`` if the caller
    prefers an OpenAI embedding model.
    """

    name = "gemini-embedding-2"

    def __init__(self, dimension: int = 3072) -> None:
        self.dimension = dimension
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cache_file = Path(__file__).resolve().parents[2] / "data" / "rag_mcp" / "gemini_vector_cache.json"
        self.cache = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def embed(self, text: str) -> List[float]:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]

        from dotenv import load_dotenv

        load_dotenv()
        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY (AI Studio) is not set for CachedGeminiEmbedding.")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model=self.name,
            contents=[text],
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
        )
        vector = list(response.embeddings[0].values)

        self.cache[text_hash] = vector
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")

        return vector


class CachedOpenAIEmbedding:
    """Production provider using text-embedding-3-small, with local cache for offline tests."""
    name = "openai-text-embedding-3-small"

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.cache_file = Path(__file__).resolve().parents[2] / "data" / "rag_mcp" / "openai_vector_cache.json"
        self.cache = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _get_client(self):
        if not self.client:
            from dotenv import load_dotenv
            load_dotenv()
            self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise RuntimeError("OPENAI_API_KEY is not set for CachedOpenAIEmbedding.")
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        return self.client

    def embed(self, text: str) -> List[float]:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        client = self._get_client()
        response = client.embeddings.create(input=[text], model="text-embedding-3-small")
        vector = response.data[0].embedding
        
        self.cache[text_hash] = vector
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")
        
        return vector


def create_embedding_provider(name: str) -> EmbeddingProvider:
    if name == "local":
        return LocalEmbedding()
    if name == "gemini":
        return CachedGeminiEmbedding()
    if name == "openai":
        return CachedOpenAIEmbedding()
    raise ValueError(
        f"Unsupported embedding provider {name!r}. "
        "Implement the EmbeddingProvider port before enabling it."
    )


class LocalEmbedding:
    """Deterministic, key-free embedding for offline/dev/test and reproducible CI.

    Hashes content tokens into a fixed-dim bag-of-words vector. Not a semantic
    model: it preserves exact-token overlap (cosine of shared tokens), which is
    enough for retrieval on a controlled synthetic corpus and guarantees the
    suite runs with zero API keys. Swap to ``gemini``/``openai`` for production
    semantic recall once a billing-backed key is provisioned.
    """

    name = "local"
    _DIM = 256
    _SEED = 0x9E3779B9

    def __init__(self, dimension: int = _DIM) -> None:
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        for token in tokens(text):
            h = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")
            idx = h % self.dimension
            # Add a stable per-token magnitude so repeated tokens reinforce.
            mag = 1.0 + ((h >> 8) & 0xFF) / 255.0
            vec[idx] += mag
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            vec = [v / norm for v in vec]
        return vec
