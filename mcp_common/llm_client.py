"""Gemma 4-31B-IT client via Google AI Studio endpoint.

Wraps generateContent with timeout, retry, token limit.
Falls back to deterministic output on failure.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

from mcp_common.config import settings

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    pass


class GemmaClient:
    """Client for gemma-4-31b-it via Google Generative Language API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
    ):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.model = model or settings.GOOGLE_MODEL
        self.base_endpoint = endpoint or settings.GOOGLE_ENDPOINT
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
        self.max_output_tokens = max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS

        self._url = f"{self.base_endpoint}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """Generate content with retries. Returns text or raises LLMClientError."""
        payload = self._build_payload(prompt, system_prompt, temperature, max_output_tokens)

        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await self._client.post(self._url, json=payload)
                if resp.status_code == 401:
                    raise LLMClientError("Invalid API key (401)")
                if resp.status_code == 403:
                    raise LLMClientError("API key forbidden (403) - check model access")
                if resp.status_code == 429:
                    raise LLMClientError("Rate limited (429)")
                resp.raise_for_status()
                data = resp.json()
                return self._extract_text(data)
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_exc = e
                logger.warning(f"LLM call timeout/network error (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt < self.max_retries:
                    await self._backoff(attempt)
            except httpx.HTTPStatusError as e:
                last_exc = e
                logger.error(f"LLM HTTP error: {e.response.status_code} - {e.response.text}")
                raise LLMClientError(f"HTTP {e.response.status_code}: {e.response.text}")
            except Exception as e:
                last_exc = e
                logger.error(f"LLM unexpected error: {e}")
                break

        # All retries exhausted
        logger.error(f"LLM generate failed after {self.max_retries + 1} attempts: {last_exc}")
        raise LLMClientError(f"LLM unavailable: {last_exc}")

    def generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """Synchronous wrapper for non-async contexts (tests, fallback)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.generate(prompt, system_prompt, temperature, max_output_tokens))

    def _build_payload(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_output_tokens: Optional[int],
    ) -> Dict[str, Any]:
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        return {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens or self.max_output_tokens,
                "topP": 0.95,
                "topK": 40,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        }

    def _extract_text(self, data: Dict[str, Any]) -> str:
        """Extract text from generateContent response."""
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts).strip()
        except Exception:
            return ""

    async def _backoff(self, attempt: int) -> None:
        await __import__("asyncio").sleep(0.5 * (2 ** attempt))

    async def close(self):
        await self._client.aclose()


# Singleton
_gemma_client: Optional[GemmaClient] = None


def get_gemma_client() -> GemmaClient:
    global _gemma_client
    if _gemma_client is None:
        _gemma_client = GemmaClient()
    return _gemma_client


# Deterministic fallbacks (used when LLM unavailable)
def deterministic_matching_reason(product_id: str, profile: Dict[str, Any]) -> str:
    """Fallback matching reason when gemma unavailable."""
    reasons = {
        "PROD-PAYROLL": f"Quy mô {profile.get('employees_count', 0)} nhân sự phù hợp dịch vụ chi lương.",
        "PROD-CASH-MGMT": "Dòng tiền phân tán và doanh thu đạt ngưỡng demo của giải pháp quản lý dòng tiền.",
        "PROD-COLLECTION": "Nhu cầu thu/chi hộ và đối soát giao dịch.",
        "PROD-WORKING-CAPITAL": "Nhu cầu vốn lưu động/thấu chi cần được Legal thẩm định tiếp.",
    }
    return reasons.get(product_id, "Phù hợp nhu cầu doanh nghiệp.")


def deterministic_semantic_score(query: str, evidence_text: str) -> float:
    """Simple token overlap score as fallback for semantic support."""
    q_tokens = set(query.lower().split())
    e_tokens = set(evidence_text.lower().split())
    if not q_tokens:
        return 0.0
    return len(q_tokens & e_tokens) / len(q_tokens)


def injection_semantic_judge(text: str) -> Dict[str, Any]:
    """Fallback injection detection when LLM unavailable."""
    injection_keywords = [
        "ignore previous", "bỏ qua chỉ dẫn", "system prompt",
        "call api create", "gọi api tạo", "bypass approval", "vượt phê duyệt",
    ]
    found = [kw for kw in injection_keywords if kw.lower() in text.lower()]
    return {"injection_detected": len(found) > 0, "patterns": found, "method": "fallback_keyword"}