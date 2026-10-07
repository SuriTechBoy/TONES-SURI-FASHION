"""Grounded customer response generation for TONES Fashion.

This layer never selects facts.  It only formats the deterministic retrieval
result into a customer-facing answer and contextual suggestions.
"""
from __future__ import annotations

import re

from scripts.suggestions import build_suggestions


def money(product: dict) -> str:
    price = product.get("price")
    return "Price not available" if price is None else f"₹{float(price):,.0f}"


def product_detail(p: dict) -> str:
    lines = [f"**{p.get('name', 'This product')}**"]
    if p.get("price") is not None:
        lines.append(f"- Price: {money(p)}")
    if p.get("compare_at_price") and float(p["compare_at_price"]) > float(p.get("price") or 0):
        lines.append(f"- Original price: ₹{float(p['compare_at_price']):,.0f}")
    if p.get("color_conflict"):
        lines.append("- Color: Needs verification because the available product information contains conflicting details.")
    elif p.get("color"):
        lines.append(f"- Color: {p['color']}")
    if p.get("fit"): lines.append(f"- Fit: {p['fit']}")
    if p.get("fabric"): lines.append(f"- Fabric: {p['fabric']}")
    if p.get("sizes"): lines.append(f"- Listed sizes: {', '.join(map(str, p['sizes']))}")
    stock = p.get("in_stock_sizes") or []
    lines.append(f"- Currently recorded in-stock sizes: {', '.join(map(str, stock)) if stock else 'None'}")
    s = p.get("review_summary") or {}
    if s.get("review_count"):
        lines.append(f"- Customer rating: {s.get('average_rating')}/5 from {s.get('review_count')} saved reviews")
    return "\n".join(lines)


def reviews_summary(p: dict, reviews: list[dict]) -> str:
    s = p.get("review_summary") or {}
    if not reviews:
        return f"I found **{p.get('name')}**, but there are no saved customer reviews for it in the current knowledge snapshot."
    return f"I found **{p.get('name')}** with a saved rating of **{s.get('average_rating', '-')} / 5** from **{s.get('review_count', len(reviews))} reviews**."


def choose_business(retrieval: dict) -> dict | None:
    intent = retrieval.get("intent")
    q = retrieval.get("query", "").lower()
    mapping = {
        "RETURN_EXCHANGE": "return_exchange_policy", "SHIPPING": "shipping_policy",
        "ORDER_TRACKING": "order_tracking", "CANCELLATION": "return_exchange_policy",
        "PAYMENTS": "payment_methods", "CONTACT": "customer_support",
    }
    topic = mapping.get(intent)
    if intent == "BRAND_BUSINESS":
        if any(x in q for x in ["owner", "owns", "owned by", "founder"]): topic = "ownership"
        elif any(x in q for x in ["profit", "revenue", "income"]): topic = "financial_information"
        elif any(x in q for x in ["hyderabad", "based in", "where is tones"]): topic = "business_location"
        elif any(x in q for x in ["categories", "what do you sell", "what products do you sell"]): topic = "product_categories"
        elif any(x in q for x in ["why choose", "special", "different", "unique", "indian men"]): topic = "brand_differentiation"
        else: topic = "brand_identity"
    if topic:
        for record in retrieval.get("business", []):
            if record.get("topic") == topic:
                return record
    return retrieval.get("business", [None])[0]


def no_match_answer(retrieval: dict) -> str:
    if retrieval.get("needs_clarification") and retrieval.get("clarification_reason") == "budget_amount_missing":
        return "What budget would you like to shop within? For example, **under ₹1000**."
    f = retrieval.get("filters") or {}
    if retrieval.get("unsupported_gender_filter"):
        return "I couldn't find a verified TONES product matching all of those requirements because gender information is not currently verified in the product catalogue."
    bits = []
    if f.get("color"): bits.append(str(f["color"]).lower())
    if f.get("fit"): bits.append(str(f["fit"]).lower())
    if f.get("product_type"): bits.append(f["product_type"].replace("t-shirt", "T-shirt"))
    if f.get("gender"): bits.append(f["gender"])
    if f.get("max_price") is not None: bits.append(f"under ₹{f['max_price']:,.0f}")
    if f.get("min_price") is not None and f.get("max_price") is not None:
        bits[-1] = f"between ₹{f['min_price']:,.0f} and ₹{f['max_price']:,.0f}"
    if f.get("size"): bits.append(f"in {f['size']}")
    label = " ".join(bits).strip()
    return f"I couldn't find an exact TONES product match{(' for ' + label) if label else ''} in the current knowledge snapshot. I won't substitute an unrelated product."


def _requested_size(q: str) -> str | None:
    m = re.search(r"\b(2xl|xxl|xl|l|m|s)\b", q, re.I)
    return m.group(1).upper() if m else None


def _with_suggestions(result: dict, retrieval: dict) -> dict:
    result["suggested_questions"] = build_suggestions(retrieval, result.get("answer", ""))
    return result


def generate(retrieval: dict) -> dict:
    intent = retrieval.get("intent")
    route = retrieval.get("route")

    if route == "OUT_OF_SCOPE":
        return _with_suggestions({
            "answer": "I’m here to help with TONES Fashion products, orders, policies, reviews, and verified TONES information. I don’t have information about that topic.",
            "response_type": "text",
        }, retrieval)

    if retrieval.get("needs_clarification"):
        if retrieval.get("clarification_reason") == "budget_amount_missing":
            return _with_suggestions({
                "answer": "What budget would you like to shop within? For example, **under ₹1000**.",
                "response_type": "text",
            }, retrieval)
        return _with_suggestions({
            "answer": "Which TONES product are you asking about? Please give me the product name so I can answer from the correct product record.",
            "response_type": "text",
        }, retrieval)

    if intent == "PRODUCT_REVIEWS":
        p = retrieval.get("product"); reviews = retrieval.get("reviews", [])
        if not p or retrieval.get("entity_confidence", 0) < 0.80:
            return _with_suggestions({
                "answer": "I couldn't match that product to the current TONES catalogue, so I won't substitute a different product.",
                "response_type": "text",
            }, retrieval)
        return _with_suggestions({
            "answer": reviews_summary(p, reviews),
            "response_type": "reviews", "product": p, "reviews": reviews,
        }, retrieval)

    if intent in {"PRODUCT_DETAILS", "PRODUCT_ATTRIBUTE"}:
        p = retrieval.get("product")
        if not p:
            return _with_suggestions({
                "answer": "Which TONES product are you asking about? Please give me the product name.",
                "response_type": "text",
            }, retrieval)
        q = retrieval.get("query", "").lower()
        if intent == "PRODUCT_DETAILS" or any(x in q for x in ["everything", "details", "detail about", "information about"]):
            return _with_suggestions({
                "answer": product_detail(p) + "\n\n" + reviews_summary(p, retrieval.get("reviews", [])),
                "response_type": "product", "products": [p], "reviews": retrieval.get("reviews", []),
            }, retrieval)
        if "fabric" in q or "material" in q:
            return _with_suggestions({"answer": f"The fabric listed for **{p['name']}** is **{p.get('fabric') or 'not available'}**.", "response_type": "product", "products": [p]}, retrieval)
        if "size" in q or "sizes" in q:
            listed = ", ".join(map(str, p.get("sizes", []))) or "not listed"
            stock = ", ".join(map(str, p.get("in_stock_sizes", []))) or "none"
            wanted = retrieval.get("filters", {}).get("size") or _requested_size(q)
            if wanted:
                available = wanted in {str(x).upper() for x in p.get("in_stock_sizes", [])}
                return _with_suggestions({
                    "answer": f"**{p['name']}** is {'currently recorded as in stock' if available else 'not currently recorded as in stock'} in size **{wanted}**. Listed sizes are: **{listed}**.",
                    "response_type": "product", "products": [p],
                }, retrieval)
            return _with_suggestions({
                "answer": f"**{p['name']}** has these listed sizes: **{listed}**. Currently recorded in-stock sizes: **{stock}**.",
                "response_type": "product", "products": [p],
            }, retrieval)
        if "stock" in q or "available" in q:
            stock = ", ".join(map(str, p.get("in_stock_sizes", []))) or "none"
            return _with_suggestions({
                "answer": f"**{p['name']}** is currently recorded in stock in: **{stock}**. Other listed sizes are not currently recorded as in stock in this snapshot.",
                "response_type": "product", "products": [p],
            }, retrieval)
        if "price" in q or "cost" in q:
            return _with_suggestions({"answer": f"The price of **{p['name']}** is **{money(p)}**.", "response_type": "product", "products": [p]}, retrieval)
        if "color" in q or "colour" in q:
            if p.get("color_conflict"):
                ans = "Color information needs verification because the available product information contains conflicting details."
            else:
                ans = f"The listed color for **{p['name']}** is **{p.get('color') or 'not available'}**."
            return _with_suggestions({"answer": ans, "response_type": "product", "products": [p]}, retrieval)
        if "fit" in q:
            return _with_suggestions({"answer": f"The listed fit for **{p['name']}** is **{p.get('fit') or 'not available'}**.", "response_type": "product", "products": [p]}, retrieval)
        return _with_suggestions({"answer": product_detail(p), "response_type": "product", "products": [p]}, retrieval)

    if intent == "PRODUCT_SEARCH":
        products = retrieval.get("products", [])
        if not products:
            return _with_suggestions({"answer": no_match_answer(retrieval), "response_type": "text"}, retrieval)
        if retrieval.get("product") and retrieval.get("entity_confidence", 0) >= 0.96:
            return _with_suggestions({"answer": product_detail(retrieval["product"]), "response_type": "product", "products": [retrieval["product"]]}, retrieval)
        return _with_suggestions({
            "answer": "Here are the verified TONES products matching all of your requested conditions:",
            "response_type": "product_list", "products": products,
        }, retrieval)

    if intent == "CHEAPEST_PRODUCT":
        products = retrieval.get("products", [])
        return _with_suggestions({"answer": "The cheapest verified product(s) in the current catalogue are:", "response_type": "product_list", "products": products}, retrieval)

    if intent == "MOST_EXPENSIVE_PRODUCT":
        products = retrieval.get("products", [])
        return _with_suggestions({"answer": "The highest-priced verified product(s) in the current catalogue are:", "response_type": "product_list", "products": products}, retrieval)

    if intent == "PRODUCT_OFFERS":
        products = retrieval.get("products", [])
        promo = next((b for b in retrieval.get("business", []) if b.get("topic") == "current_promotions"), None)
        ans = "Current verified TONES promotions are shown below." if promo else "I found these verified products currently recorded as on sale."
        return _with_suggestions({"answer": ans, "response_type": "product_list" if products else "business", "products": products, "business": [promo] if promo else []}, retrieval)

    if intent in {"RETURN_EXCHANGE", "SHIPPING", "ORDER_TRACKING", "CANCELLATION", "PAYMENTS", "CONTACT", "BRAND_BUSINESS"}:
        record = choose_business(retrieval)
        if not record or not record.get("facts"):
            if intent == "PAYMENTS":
                ans = "I couldn’t confirm the available payment methods from the verified TONES Fashion information available to me. Please check the payment options shown at checkout."
            else:
                ans = "I don't currently have verified information about that in the TONES Fashion knowledge available to me."
            return _with_suggestions({"answer": ans, "response_type": "text"}, retrieval)

        q = retrieval.get("query", "").lower()
        status = record.get("status", "")
        topic = record.get("topic")
        if topic == "ownership":
            ans = "I couldn't find verified information about the owner or founder of TONES Fashion in the current public knowledge snapshot. I don't want to guess."
        elif topic == "financial_information":
            ans = "I couldn't find a verified public figure for TONES Fashion's profit or revenue in the current knowledge snapshot. I don't want to guess."
        elif status == "NEEDS_VERIFICATION":
            ans = "I couldn’t confirm that from the verified TONES Fashion information available to me. Please check the official website or checkout for the latest details."
        elif topic == "business_location":
            ans = "Yes. TONES Fashion is a Hyderabad-based homegrown menswear/streetwear brand."
        elif topic == "product_categories":
            ans = "TONES Fashion's website navigation includes Kurtas, Shirts, T-Shirts & Sweatshirts, and Bottom Wear. It also has New Launch, Best Sellers, and Designer Wear sections."
        else:
            ans = "\n".join(f"- {f}" for f in record.get("facts", []))
        return _with_suggestions({"answer": ans, "response_type": "business", "business": [record]}, retrieval)

    return _with_suggestions({
        "answer": "I can help with TONES Fashion products and verified brand/store information. Please rephrase your question with a TONES product or topic.",
        "response_type": "text",
    }, retrieval)
