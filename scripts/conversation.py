"""MRU-inspired conversation handling for TONES.

This module is deliberately deterministic.  It does not ask an LLM to decide
what the user meant when the previous turn already gives us enough context.
"""
from __future__ import annotations

import re
from typing import Any


def norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def is_short_followup(query: str) -> bool:
    q = norm(query)
    if not q:
        return False
    words = q.split()
    markers = (
        "only ", "just ", "these", "those", "ones", "what about", "which one",
        "which ones", "under ", "below ", "above ", "over ", "between ",
        "in xl", "in l", "in m", "in s", "available", "in stock",
        "reviews", "review", "price", "cost", "size", "sizes", "fabric",
        "material", "fit", "color", "colour", "stock",
    )
    return len(words) <= 8 and any(q == m.strip() or q.startswith(m) for m in markers)


def standalone_query(query: str, context: dict | None) -> str:
    """Create a retrieval-friendly standalone query from the latest turn.

    We preserve a complete current question and only inherit context for
    clearly fragmentary follow-ups.  This mirrors the useful part of MRU's
    query-rewriter while avoiding an external LLM dependency.
    """
    q = str(query or "").strip()
    if not context:
        return q

    product = context.get("product") or {}
    product_name = str(product.get("name") or "").strip()
    previous_filters = context.get("filters") or {}

    if product_name and is_short_followup(q):
        return f"{q} for {product_name}"

    if previous_filters and is_short_followup(q):
        pieces = []
        if previous_filters.get("color"):
            pieces.append(str(previous_filters["color"]))
        if previous_filters.get("product_type"):
            pieces.append(str(previous_filters["product_type"]))
        if previous_filters.get("gender"):
            pieces.append(str(previous_filters["gender"]))
        if pieces:
            return f"{q} {' '.join(pieces)}"

    return q


def merge_product_context(current_filters: dict, context: dict | None, *, exact_entity: bool) -> dict:
    """Merge only safe shopping constraints from the previous turn."""
    if exact_entity or not context:
        return dict(current_filters)
    previous = context.get("filters") or {}
    merged = dict(previous)
    merged.update(current_filters)
    return merged
