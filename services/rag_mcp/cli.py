"""Administrative CLI kept outside the LLM-visible MCP tool allowlist."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from services.rag_mcp.config import settings
from services.rag_mcp.service import RagKnowledgeService


def main() -> None:
    parser = argparse.ArgumentParser(description="Governed RAG MCP administration")
    parser.add_argument("command", choices=["seed", "health", "audit"])
    parser.add_argument("--db", type=Path, default=settings.db_path)
    parser.add_argument("--trace-id")
    args = parser.parse_args()
    runtime = replace(settings, db_path=args.db)
    service = RagKnowledgeService(settings=runtime)
    if args.command == "seed":
        payload = service.ingestor.seed().model_dump(mode="json")
    elif args.command == "health":
        payload = service.health().model_dump(mode="json")
    else:
        if not args.trace_id:
            parser.error("--trace-id is required for audit")
        payload = service.store.audit_events(args.trace_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
