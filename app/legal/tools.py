"""Extended Legal Tools (Aligned with plan_v3 Bảng A1).

Tái sử dụng công cụ cũ để tương thích ngược, đồng thời bổ sung các công cụ mới.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Re-export old tools for backward compatibility
# ---------------------------------------------------------------------------
from app.tools.legal_tools import (
    SYNTHETIC_COMPLIANCE_POLICIES,
    validate_business_registration,
    check_document_expiry,
    search_compliance_policy,
)

# ---------------------------------------------------------------------------
# New Tools (Mock implementations for demo)
# ---------------------------------------------------------------------------

def validate_documents(documents: List[Dict[str, Any]], required_doc_types: List[str]) -> Dict[str, Any]:
    """Kiểm tra tính đầy đủ và hiệu lực của bộ hồ sơ pháp lý."""
    present_types = [d.get("document_type_id") for d in documents if d.get("document_type_id")]
    missing = [t for t in required_doc_types if t not in present_types]
    
    expired = []
    for d in documents:
        if d.get("is_expired"):
            expired.append(d.get("document_type_id", "Unknown"))
            
    return {
        "is_complete": len(missing) == 0,
        "missing_documents": missing,
        "has_expired_documents": len(expired) > 0,
        "expired_documents": expired
    }

def check_representative_and_ubo(company_profile: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Kiểm tra người đại diện và UBO."""
    rep = company_profile.get("representative", {})
    ubo_status = company_profile.get("ubo_status", "unknown")
    
    has_rep_info = bool(rep.get("name") and rep.get("id_number"))
    
    return {
        "representative_complete": has_rep_info,
        "ubo_complete": ubo_status == "complete",
        "ubo_status": ubo_status,
        "issues": [] if has_rep_info and ubo_status == "complete" else ["Missing representative or UBO information"]
    }

def screen_watchlist(company_name: str, tax_code: str, representatives: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sàng lọc danh sách cấm vận và PEP (Demo Synthetic)."""
    watchlist_path = Path("data/legal/watchlist/synthetic_watchlist.json")
    
    match_found = False
    reason = ""
    matched_entity = None
    
    if watchlist_path.exists():
        try:
            with open(watchlist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Check sanctions
            for s in data.get("sanctions", []):
                if s.get("tax_code") == tax_code:
                    match_found = True
                    reason = s.get("reason", "Watchlist match")
                    matched_entity = s
                    break
                    
                # Simple name match
                cname = company_name.lower().strip()
                sname = s.get("name", "").lower().strip()
                if cname and sname and (cname == sname or sname in cname):
                    match_found = True
                    reason = s.get("reason", "Watchlist match")
                    matched_entity = s
                    break
                    
            # Check PEP (if we had representative detailed info, we'd check here)
            # For demo, just check if any representative name matches exactly
            rep_names = [r.get("name", "").lower().strip() for r in representatives if r.get("name")]
            if not match_found:
                for p in data.get("pep", []):
                    pname = p.get("name", "").lower().strip()
                    if pname and pname in rep_names:
                        match_found = True
                        reason = f"PEP Match: {p.get('position', '')}"
                        matched_entity = p
                        break
                        
        except Exception as e:
            pass # Fail open or fail closed? For screening, usually fail closed, but this is a mock.
            
    return {
        "screened": True,
        "match_found": match_found,
        "reason": reason,
        "matched_entity": matched_entity
    }
