"""
TONES Fashion - Intent / Answer Library

Purpose:
    Reuse existing verified knowledge for semantically similar customer questions.
    This module is deliberately independent from the existing query router so it
    can be integrated without duplicating canonical knowledge.

Integration idea:
    query -> detect_special_intent(query)
          -> if an intent is returned, use its knowledge_ids / operation
          -> otherwise continue with the existing PRODUCT/BUSINESS/MIXED/GENERAL flow
"""

import re
from typing import Any, Dict, Optional


INTENT_RULES = {
    "RETURN_POLICY": [
        r"\breturn\b.*\b(product|item|order)\b",
        r"\b(return policy|return available|send .* back)\b",
    ],
    "EXCHANGE_POLICY": [
        r"\bexchange\b.*\b(product|item|order)\b",
        r"\b(exchange policy|exchange available)\b",
    ],
    "ORDER_CANCELLATION": [
        r"\bcancel\b.*\border\b",
        r"\border\b.*\bcancel\b",
    ],
    "ORDER_TRACKING": [
        r"\btrack\b.*\border\b",
        r"\border\b.*\btracking\b",
    ],
    "ORDER_STATUS": [
        r"\b(order status|status of my order)\b",
        r"\bwhere is my order\b",
        r"\bhas my order shipped\b",
    ],
    "SHIPPING_POLICY": [
        r"\bshipping\b",
        r"\bdelivery\b.*\b(take|time|days|india)\b",
        r"\bdeliver\b.*\bindia\b",
    ],
    "CONTACT_INFO": [
        r"\b(contact|customer support|support email|email address)\b",
    ],
    "CHEAPEST_PRODUCT": [
        r"\b(cheapest|lowest[- ]priced|lowest price)\b.*\b(product|item)\b",
    ],
    "MOST_EXPENSIVE_PRODUCT": [
        r"\b(most expensive|highest[- ]priced|highest price)\b.*\b(product|item)\b",
    ],
    "PRODUCT_FABRIC": [
        r"\bwhat\b.*\bfabric\b",
        r"\bwhat\b.*\bmaterial\b",
        r"\bfabric\b.*\b(product|item|shirt|tee|t[- ]shirt)\b",
    ],
    "PRODUCT_SIZE": [
        r"\bwhat sizes\b",
        r"\bwhich sizes\b",
        r"\bsizes\b.*\bavailable\b",
    ],
    "PRODUCTS_ON_SALE": [
        r"\b(on sale|on discount|discounted products?)\b",
    ],
}


INTENT_CONFIG = {
    "RETURN_POLICY": {
        "knowledge_ids": ["TONES-KB-RETURNS-001"],
        "suppress_product_results": True,
        "answer_mode": "reuse_verified_facts",
    },
    "EXCHANGE_POLICY": {
        "knowledge_ids": ["TONES-KB-RETURNS-001"],
        "suppress_product_results": True,
        "answer_mode": "reuse_verified_facts",
    },
    "ORDER_CANCELLATION": {
        "knowledge_ids": ["TONES-KB-RETURNS-001", "TONES-KB-SHIPPING-001"],
        "suppress_product_results": True,
        "answer_mode": "reuse_relevant_verified_facts",
        "fact_keywords": ("cancel", "cancelled", "canceled", "dispatch"),
    },
    "ORDER_TRACKING": {
        "knowledge_ids": ["TONES-KB-ORDER-TRACKING-001"],
        "suppress_product_results": True,
        "answer_mode": "reuse_verified_facts",
    },
    "ORDER_STATUS": {
        "knowledge_ids": ["TONES-KB-ORDER-TRACKING-001"],
        "suppress_product_results": True,
        "answer_mode": "live_status_unavailable_from_static_kb",
    },
    "SHIPPING_POLICY": {
        "knowledge_ids": ["TONES-KB-SHIPPING-001"],
        "suppress_product_results": True,
        "answer_mode": "reuse_verified_facts",
    },
    "CONTACT_INFO": {
        "knowledge_ids": ["TONES-KB-CONTACT-001"],
        "suppress_product_results": True,
        "answer_mode": "reuse_verified_facts",
    },
    "CHEAPEST_PRODUCT": {
        "knowledge_ids": [],
        "suppress_product_results": True,
        "answer_mode": "structured_aggregation",
        "operation": "MIN(price)",
    },
    "MOST_EXPENSIVE_PRODUCT": {
        "knowledge_ids": [],
        "suppress_product_results": True,
        "answer_mode": "structured_aggregation",
        "operation": "MAX(price)",
    },
    "PRODUCT_FABRIC": {
        "knowledge_ids": [],
        "suppress_product_results_when_product_missing": True,
        "answer_mode": "product_attribute_lookup",
        "attribute": "fabric",
    },
    "PRODUCT_SIZE": {
        "knowledge_ids": [],
        "suppress_product_results_when_product_missing": True,
        "answer_mode": "product_attribute_lookup",
        "attribute": "variant_sizes",
    },
    "PRODUCTS_ON_SALE": {
        "knowledge_ids": [],
        "answer_mode": "structured_filter",
        "operation": "compare_at_price > displayed_price",
    },
}


def detect_intent(query: str) -> Optional[str]:
    """Return the highest-priority special intent, or None."""
    q = (query or "").strip().lower()

    # Most specific / safety-sensitive intents first.
    priority = [
        "ORDER_STATUS",
        "ORDER_TRACKING",
        "ORDER_CANCELLATION",
        "RETURN_POLICY",
        "EXCHANGE_POLICY",
        "CHEAPEST_PRODUCT",
        "MOST_EXPENSIVE_PRODUCT",
        "PRODUCT_FABRIC",
        "PRODUCT_SIZE",
        "PRODUCTS_ON_SALE",
        "SHIPPING_POLICY",
        "CONTACT_INFO",
    ]

    for intent in priority:
        for pattern in INTENT_RULES[intent]:
            if re.search(pattern, q, re.IGNORECASE):
                return intent

    return None


def get_intent_config(intent: Optional[str]) -> Dict[str, Any]:
    if not intent:
        return {}
    return dict(INTENT_CONFIG.get(intent, {}))


def filter_business_facts(
    facts: list[str],
    intent: str,
) -> list[str]:
    """Keep only directly relevant existing facts for narrow intents."""
    if intent != "ORDER_CANCELLATION":
        return list(facts)

    keywords = INTENT_CONFIG[intent]["fact_keywords"]
    selected = [
        fact for fact in facts
        if any(word in fact.lower() for word in keywords)
    ]
    return selected


def missing_product_attribute_response(intent: str) -> str:
    attribute = INTENT_CONFIG[intent]["attribute"]

    if attribute == "fabric":
        return (
            "Which product are you asking about? Please give me the "
            "product name, and I can check its recorded fabric information."
        )

    if attribute == "variant_sizes":
        return (
            "Which product are you asking about? Please give me the "
            "product name, and I can check its recorded size information."
        )

    return "Which product are you asking about?"


if __name__ == "__main__":
    tests = [
        "Can I return a product?",
        "Can I exchange a product?",
        "Can I cancel my order?",
        "How can I track my order?",
        "What is my order status?",
        "Do you deliver across India?",
        "How can I contact TONES Fashion?",
        "What is the cheapest product you have?",
        "What is the fabric of the product?",
        "What sizes are available?",
        "Show me products on sale",
        "Show me black t-shirts",
    ]

    for question in tests:
        intent = detect_intent(question)
        print(f"{question}\n  -> {intent or 'EXISTING PRODUCT/BUSINESS ROUTER'}")