# Backend Deploy Limitation — IPv6-only LXC

## Status

The backend (`app/` + `services/rag_mcp`) is **code-complete, wired, and
test-green** on `main`. It is **not deployed** to a public endpoint.

## Why it is not deployed

The target host is an LXC container on the VPS (`sgp1.w9.nu`) with:

- **IPv6 only** on the container itself.
- **IPv4 reachable only via NAT SSH** (`ssh -p 2204 root@sgp1.w9.nu`), used for
  shell access and port-forwarding — not for inbound HTTP from the public
  internet.

There is **no tunnel** from the container to `vaic-api.w9.nu`. Without a stable
ingress (reverse proxy / Cloudflare Tunnel / IPv4 NAT port map), the FastAPI
app cannot be reached at `https://vaic-api.w9.nu`. This is an **infra/network
constraint**, not a code defect.

## What works without deploy

- Full offline test suite (unit / contract / rag_mcp / e2e / api_v2 /
  evaluation / benchmark) — see `.github/workflows/ci.yml`.
- Embedding via Google AI Studio (`gemini-embedding-2`) with a **local cache**,
  so a warmed cache serves requests with **zero network calls**.
- LLM intent extraction via `gemma-4-31b-it` through the AI Studio OpenAI-
  compatible endpoint; deterministic fallback when `INTENT_USE_LLM=false`.

## To deploy later (outside this task)

1. Establish ingress on the VPS: Cloudflare Tunnel, or an IPv4 NAT rule
   (`VPS_PORT` → container `PORT`), or enable IPv6 routing for the container.
2. Run: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
3. Point `vaic-api.w9.nu` at that ingress; set `GOOGLE_API_KEY` (AI Studio key)
   and `APPROVAL_SECRET` as environment secrets.
4. The Flutter app reads `kDefaultBaseUrl` in
   `lib/core/api_config.dart`; flip `useMock` to `false` once the endpoint is
   reachable.

## Verification of this state

```
flutter analyze            # No issues found
pytest tests/unit tests/contract tests/rag_mcp   # 244 passed (gemini, cached)
pytest tests/test_sales_cases_e2e.py tests/test_api_v2.py  # 18 passed
python -m app.evaluation.runner ...               # passed: true
python -m benchmarks.run --cache-mode warm ...    # passed
```
