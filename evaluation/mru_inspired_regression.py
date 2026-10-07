"""Regression suite for the MRU-inspired TONES architecture.

Focus: intent routing, exact entity resolution, hard filters, stock semantics,
business grounding, out-of-scope safety, and conversation follow-ups.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.tones_engine import retrieve, product_matches
from scripts.answer_generator import generate

CASES = [
    ("Show me a red t-shirt", "PRODUCT_SEARCH"),
    ("Show me black t-shirts under ₹800", "PRODUCT_SEARCH"),
    ("Show me XL t-shirts that are in stock", "PRODUCT_SEARCH"),
    ("Show me oversized t-shirts under ₹1000", "PRODUCT_SEARCH"),
    ("Show me products under ₹500", "PRODUCT_SEARCH"),
    ("What is the cheapest TONES product?", "CHEAPEST_PRODUCT"),
    ("What is the most expensive TONES product?", "MOST_EXPENSIVE_PRODUCT"),
    ("Show me products on sale", "PRODUCT_OFFERS"),
    ("Tell me everything about Tones Original Black", "PRODUCT_DETAILS"),
    ("What fabric is Tones Original Black?", "PRODUCT_ATTRIBUTE"),
    ("What sizes are available for Tones Original Black?", "PRODUCT_ATTRIBUTE"),
    ("Is Tones Original Black in stock?", "PRODUCT_ATTRIBUTE"),
    ("Is Tones Original Black available in size M?", "PRODUCT_ATTRIBUTE"),
    ("Is XXL available for Tones Original Black?", "PRODUCT_ATTRIBUTE"),
    ("What is the price of Tones Original Black?", "PRODUCT_ATTRIBUTE"),
    ("What is the color of Tones Original Black?", "PRODUCT_ATTRIBUTE"),
    ("What do customers say about Tones Original Black?", "PRODUCT_REVIEWS"),
    ("What is the rating of Daily Tees - orange?", "PRODUCT_REVIEWS"),
    ("Is TONES Fashion based in Hyderabad?", "BRAND_BUSINESS"),
    ("Who owns TONES Fashion?", "BRAND_BUSINESS"),
    ("What is TONES Fashion?", "BRAND_BUSINESS"),
    ("Why should I choose TONES Fashion?", "BRAND_BUSINESS"),
    ("How do I contact TONES Fashion?", "CONTACT"),
    ("How long does shipping take?", "SHIPPING"),
    ("What is your return policy?", "RETURN_EXCHANGE"),
    ("How can I track my order?", "ORDER_TRACKING"),
    ("Can I cancel my order?", "CANCELLATION"),
    ("Can I pay using COD?", "PAYMENTS"),
    ("What is the TFV25 offer?", "PRODUCT_OFFERS"),
    ("Show me men's t-shirts", "PRODUCT_SEARCH"),
    ("Show me women's dresses", "PRODUCT_SEARCH"),
    ("Show me red men's t-shirts under ₹1000", "PRODUCT_SEARCH"),
    ("Show me a red women's dress under ₹500", "PRODUCT_SEARCH"),
    ("Show me Nike products", "OUT_OF_SCOPE"),
    ("Show me smartphones", "OUT_OF_SCOPE"),
    ("Explain Python loops", "OUT_OF_SCOPE"),
    ("What is the capital of India?", "OUT_OF_SCOPE"),
    ("Show me products in my budget", "PRODUCT_SEARCH"),
]


def check() -> list[dict]:
    rows = []
    for q, expected in CASES:
        r = retrieve(q)
        g = generate(r)
        ok = r["intent"] == expected
        reason = ""
        if expected == "OUT_OF_SCOPE":
            ok = ok and r["route"] == "OUT_OF_SCOPE" and not r["products"]
        if expected == "PRODUCT_SEARCH":
            for p in r["products"]:
                valid, _ = product_matches(p, r["filters"], q)
                if not valid:
                    ok = False
                    reason = f"invalid result: {p.get('name')}"
                    break
            if not r["products"] and "budget" not in q.lower():
                ok = ok and bool(g["answer"])
        if q.startswith("Tell me everything about"):
            ok = ok and bool(r.get("product")) and len(r.get("reviews", [])) > 0
        if "Tones Original Black" in q and "sizes" in q.lower():
            ok = ok and r.get("filters", {}).get("size") is None and "S, M, L, XL, XXL" in g["answer"]
        if "size M" in q:
            ok = ok and "not currently recorded as in stock" in g["answer"]
        if "XXL available" in q:
            ok = ok and "currently recorded in stock" in g["answer"]
        if "owner" in q.lower():
            ok = ok and "verified information" in g["answer"].lower()
        if "COD" in q:
            ok = ok and "couldn’t confirm" in g["answer"]
        rows.append({"question": q, "pass": ok, "reason": reason, "intent": r["intent"]})

    # Conversation tests modelled on MRU's follow-up behavior.
    r1 = retrieve("Show me black t-shirts under ₹1000")
    ctx = {
        "filters": r1["filters"],
        "product_ids": [p["product_id"] for p in r1["products"]],
        "product": None,
        "intent": r1["intent"],
    }
    r2 = retrieve("Only oversized ones", context=ctx)
    rows.append({
        "question": "FOLLOW-UP: Only oversized ones",
        "pass": r2["intent"] == "PRODUCT_SEARCH" and r2["filters"].get("color") == "Black" and r2["filters"].get("fit") == "oversized",
        "reason": "",
        "intent": r2["intent"],
    })
    r3 = retrieve("under ₹700", context=ctx)
    rows.append({
        "question": "FOLLOW-UP: under ₹700",
        "pass": r3["intent"] == "PRODUCT_SEARCH" and r3["filters"].get("product_type") == "t-shirt" and r3["filters"].get("max_price") == 700.0,
        "reason": "",
        "intent": r3["intent"],
    })
    p = retrieve("Tell me everything about Tones Original Black")
    pctx = {
        "filters": p["filters"], "product_ids": [], "product": p["product"], "intent": p["intent"]
    }
    r4 = retrieve("What sizes are available?", context=pctx)
    rows.append({
        "question": "FOLLOW-UP: What sizes are available?",
        "pass": r4["intent"] == "PRODUCT_ATTRIBUTE" and r4.get("product", {}).get("product_id") == "TONES-PROD-URL-0003",
        "reason": "",
        "intent": r4["intent"],
    })
    return rows


def main() -> None:
    rows = check()
    passed = sum(x["pass"] for x in rows)
    report = {
        "total": len(rows), "passed": passed, "failed": len(rows) - passed,
        "accuracy": round(passed / len(rows), 4), "results": rows,
    }
    out = Path(__file__).with_name("mru_inspired_regression_report.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["total", "passed", "failed", "accuracy"]}, indent=2))
    for row in rows:
        if not row["pass"]:
            print("FAIL", row)
    raise SystemExit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
