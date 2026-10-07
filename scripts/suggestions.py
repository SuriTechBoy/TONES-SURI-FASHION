"""Deterministic contextual suggested questions for TONES.

MRU generates follow-ups after each answer.  TONES uses verified templates so
suggestions never invent product attributes, policies or unsupported facts.
"""
from __future__ import annotations


def _unique(items: list[str], current: str) -> list[str]:
    seen = set()
    current_n = " ".join(str(current or "").lower().split())
    out = []
    for item in items:
        clean = " ".join(str(item or "").strip().split())
        key = clean.lower()
        if not clean or key == current_n or key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out[:2]


def build_suggestions(retrieval: dict, answer: str = "") -> list[str]:
    intent = retrieval.get("intent")
    query = retrieval.get("query", "")
    product = retrieval.get("product")
    products = retrieval.get("products") or []
    name = str((product or {}).get("name") or "").strip()
    if not name and len(products) == 1:
        name = str(products[0].get("name") or "").strip()

    if intent == "PRODUCT_DETAILS" and name:
        return _unique([
            f"What sizes are available for {name}?",
            f"What do customers say about {name}?",
        ], query)

    if intent == "PRODUCT_ATTRIBUTE" and name:
        return _unique([
            f"What do customers say about {name}?",
            f"What sizes are available for {name}?",
        ], query)

    if intent == "PRODUCT_REVIEWS" and name:
        return _unique([
            f"What is the price of {name}?",
            f"What sizes are available for {name}?",
        ], query)

    if intent in {"PRODUCT_SEARCH", "CHEAPEST_PRODUCT", "MOST_EXPENSIVE_PRODUCT", "PRODUCT_OFFERS"}:
        if products:
            p = products[0]
            pname = str(p.get("name") or "").strip()
            if pname:
                return _unique([
                    f"Tell me everything about {pname}",
                    f"What do customers say about {pname}?",
                ], query)
        return _unique([
            "Show me black t-shirts under ₹1000",
            "Show me oversized t-shirts",
        ], query)

    if intent == "SHIPPING":
        return _unique([
            "What is your return policy?",
            "How can I track my order?",
        ], query)

    if intent == "RETURN_EXCHANGE":
        return _unique([
            "How do I start a return?",
            "Can I exchange an item?",
        ], query)

    if intent == "ORDER_TRACKING":
        return _unique([
            "How long does delivery take?",
            "Can I change my address before dispatch?",
        ], query)

    if intent == "CONTACT":
        return _unique([
            "What is the customer support email?",
            "How long does delivery take?",
        ], query)

    if intent == "PAYMENTS":
        return _unique([
            "What is your return policy?",
            "How much is shipping?",
        ], query)

    if intent == "BRAND_BUSINESS":
        return _unique([
            "What products does TONES Fashion sell?",
            "How can I contact TONES Fashion?",
        ], query)

    return []
