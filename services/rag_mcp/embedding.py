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
    """Production provider using gemini-embedding-001, with local cache for offline tests.

    "text-embedding-004" (the model this class originally called) has been
    retired: calling it now returns 404 NOT_FOUND. Verified against the live
    API on 2026-07-18: `GET v1beta/models` lists gemini-embedding-001,
    gemini-embedding-2-preview and gemini-embedding-2 as the models this key
    can actually call. gemini-embedding-001 defaults to a 3072-dim output;
    outputDimensionality truncates it (Matryoshka-style) to match the
    dimension declared here so cosine() never silently compares
    mismatched-length vectors.
    """
    name = "gemini-embedding-001"

    def __init__(self, dimension: int = 768) -> None:
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
        import urllib.error
        import urllib.request
        import json as json_lib

        load_dotenv()
        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set for CachedGeminiEmbedding.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.name}:embedContent?key={api_key}"
        data = json_lib.dumps({
            "model": f"models/{self.name}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.dimension,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req) as response:
                resp_body = response.read().decode('utf-8')
                result = json_lib.loads(resp_body)
                vector = result["embedding"]["values"]
        except urllib.error.HTTPError as e:
            # Surface Google's actual error body (e.g. "RESOURCE_EXHAUSTED:
            # prepayment credits depleted") instead of a bare "HTTP Error nnn".
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini Embedding API call failed ({e.code}): {body}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to call Gemini Embedding API: {e}") from e

        self.cache[text_hash] = vector
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json_lib.dumps(self.cache), encoding="utf-8")

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
    if name == "gemini":
        return CachedGeminiEmbedding()
    if name == "openai":
        return CachedOpenAIEmbedding()
    raise ValueError(
        f"Unsupported embedding provider {name!r}. "
        "Implement the EmbeddingProvider port before enabling it."
    )
