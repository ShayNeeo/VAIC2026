"""Administrative CLI kept outside the LLM-visible MCP tool allowlist."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from services.rag_mcp.config import settings, ROOT
from services.rag_mcp.service import RagKnowledgeService


def compile_catalog() -> dict:
    # Paths
    products_csv = ROOT / "data" / "raw_csv_json" / "products.csv"
    policies_csv = ROOT / "data" / "raw_csv_json" / "product_policies.csv"
    pricing_csv = ROOT / "data" / "raw_csv_json" / "product_pricing_limits.csv"
    bundles_csv = ROOT / "data" / "raw_csv_json" / "solution_bundles.csv"
    
    # Read files
    def read_csv(path):
        if not path.exists():
            return []
        with open(path, mode="r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
            
    products = read_csv(products_csv)
    policies = read_csv(policies_csv)
    pricing = read_csv(pricing_csv)
    bundles = read_csv(bundles_csv)
    
    # Group policies by product_id
    policies_by_product = {}
    for row in policies:
        p_id = row.get("product_id")
        if p_id:
            policies_by_product.setdefault(p_id, []).append({
                "policy_id": row.get("policy_id"),
                "rule_type": row.get("rule_type"),
                "condition_field": row.get("condition_field"),
                "operator": row.get("operator"),
                "threshold_value": row.get("threshold_value"),
                "severity": row.get("severity"),
                "required_evidence": row.get("required_evidence"),
                "rule_text": row.get("rule_text"),
                "effective_from": row.get("effective_from"),
                "effective_to": row.get("effective_to"),
                "version": row.get("version"),
                "owner_team": row.get("owner_team")
            })
            
    # Group pricing by product_id
    pricing_by_product = {}
    for row in pricing:
        p_id = row.get("product_id")
        if p_id:
            pricing_by_product.setdefault(p_id, []).append({
                "pricing_id": row.get("pricing_id"),
                "segment": row.get("segment"),
                "currency": row.get("currency"),
                "fee_type": row.get("fee_type"),
                "fee_amount": float(row.get("fee_amount") or 0) if row.get("fee_amount") else 0.0,
                "fee_rate_pct": float(row.get("fee_rate_pct") or 0) if row.get("fee_rate_pct") else 0.0,
                "limit_amount": float(row.get("limit_amount") or 0) if row.get("limit_amount") else None,
                "sla_business_hours": int(row.get("sla_business_hours") or 0) if row.get("sla_business_hours") else None,
                "implementation_days": int(row.get("implementation_days") or 0) if row.get("implementation_days") else None,
                "effective_from": row.get("effective_from"),
                "effective_to": row.get("effective_to")
            })
            
    # Compile products
    compiled_products = []
    for row in products:
        p_id = row.get("product_id")
        
        # Split fields
        features = [x.strip() for x in row.get("key_features", "").split(";") if x.strip()]
        prereqs = [x.strip() for x in row.get("prerequisites", "").split(";") if x.strip()]
        currencies = [x.strip() for x in row.get("supported_currencies", "").split(";") if x.strip()]
        branches = [x.strip() for x in row.get("branches", "").split(";") if x.strip()]
        if "*" in branches:
            branches = ["*"]
            
        compiled_products.append({
            "product_id": p_id,
            "product_name": row.get("product_name"),
            "product_type": row.get("product_type"),
            "description": row.get("description"),
            "target_segment": row.get("target_segment"),
            "key_features": features,
            "prerequisites": prereqs,
            "supported_currencies": currencies,
            "minimum_revenue_vnd": float(row.get("minimum_revenue_vnd") or 0) if row.get("minimum_revenue_vnd") else 0.0,
            "status": row.get("status"),
            "active": row.get("status", "").lower() == "active",
            "branches": branches,
            "source_id": row.get("source_id"),
            "pricing_limits": pricing_by_product.get(p_id, []),
            "policies": policies_by_product.get(p_id, [])
        })
        
    compiled_bundles = []
    for row in bundles:
        b_id = row.get("bundle_id")
        included_products = [x.strip() for x in row.get("included_products", "").split(";") if x.strip()]
        benefits = [x.strip() for x in row.get("bundle_benefits", "").split(";") if x.strip()]
        compiled_bundles.append({
            "bundle_id": b_id,
            "bundle_name": row.get("bundle_name"),
            "target_segment": row.get("target_segment"),
            "included_products": included_products,
            "bundle_benefits": benefits,
            "discount_description": row.get("discount_description"),
            "effective_from": row.get("effective_from"),
            "active": row.get("status", "").lower() == "active"
        })
        
    return {
        "dataset_version": "2026.07-assembled-v1",
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "products": compiled_products,
        "solution_bundles": compiled_bundles
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Governed RAG MCP administration")
    parser.add_argument("command", choices=["seed", "health", "audit", "compile"])
    parser.add_argument("--db", type=Path, default=settings.db_path)
    parser.add_argument("--trace-id")
    args = parser.parse_args()
    runtime = replace(settings, db_path=args.db)
    service = RagKnowledgeService(settings=runtime)
    
    if args.command == "seed":
        payload = service.ingestor.seed().model_dump(mode="json")
    elif args.command == "health":
        payload = service.health().model_dump(mode="json")
    elif args.command == "compile":
        payload = compile_catalog()
        output_file = ROOT / "data" / "raw_csv_json" / "products_compiled.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Success: Catalog compiled and saved to {output_file}")
        return
    else:
        if not args.trace_id:
            parser.error("--trace-id is required for audit")
        payload = service.store.audit_events(args.trace_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
