"""Validate business knowledge records for required provenance and conservative status."""
from __future__ import annotations
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "03_STRUCTURED" / "business_knowledge.json"
out = ROOT / "04_VALIDATED" / "business_knowledge_validation.csv"
records = json.loads(src.read_text(encoding="utf-8"))
rows=[]
for r in records:
    issues=[]
    for field in ("knowledge_id","domain","topic","title","source_url","source_type","status","collected_at"):
        if not r.get(field): issues.append(f"missing:{field}")
    if r.get("status") == "VERIFIED" and not r.get("facts"):
        issues.append("verified_without_facts")
    if r.get("status") == "NEEDS_VERIFICATION" and not r.get("missing"):
        issues.append("needs_verification_without_missing_register")
    rows.append({"knowledge_id":r["knowledge_id"],"domain":r["domain"],"topic":r["topic"],"status":r["status"],"validation_status":"PASS" if not issues else "REVIEW","issues":"; ".join(issues)})
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"Validated {len(rows)} business knowledge records")
print(f"Review records: {sum(r['validation_status']=='REVIEW' for r in rows)}")
print(out)
