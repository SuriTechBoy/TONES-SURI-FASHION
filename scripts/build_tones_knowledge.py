"""Build a single verified, retrieval-ready TONES knowledge corpus from the project snapshot."""
from __future__ import annotations

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
CANONICAL = BASE_DIR / "05_CANONICAL"
STRUCTURED = BASE_DIR / "03_STRUCTURED"
RAG = BASE_DIR / "06_RAG"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def extract_color_from_name(name: str) -> str | None:
    colors = [
        "black", "white", "grey", "gray", "beige", "brown", "orange", "blue",
        "navy", "green", "red", "yellow", "pink", "maroon", "mustard", "ivory",
        "khaki", "olive", "cream", "purple", "wine", "peach", "sage",
    ]
    low = name.lower()
    for color in colors:
        if re.search(rf"\b{re.escape(color)}\b", low):
            return color.title()
    return None


def main() -> None:
    products = json.loads((CANONICAL / "products_canonical_with_collections.json").read_text(encoding="utf-8"))
    search_index = {p["product_id"]: p for p in json.loads((STRUCTURED / "product_search_index.json").read_text(encoding="utf-8"))}
    raw_types = {}
    raw_dir = BASE_DIR / "01_RAW_DATA" / "products_json"
    for raw_path in raw_dir.glob("*.json"):
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            raw_types[raw_path.stem] = raw.get("type") or raw.get("product_type")
        except Exception:
            pass
    reviews = json.loads((CANONICAL / "reviews_canonical.json").read_text(encoding="utf-8"))
    business = json.loads((CANONICAL / "business_knowledge_canonical.json").read_text(encoding="utf-8"))

    reviews_by_product: dict[str, list[dict]] = {}
    for review in reviews:
        reviews_by_product.setdefault(review["product_id"], []).append(review)

    enriched = []
    documents = []

    for product in products:
        pid = product["product_id"]
        indexed = search_index.get(pid, {})
        name = norm(product.get("name"))
        description = norm(product.get("description"))
        title_color = extract_color_from_name(name)
        source_color = indexed.get("color")
        color_conflict = bool(title_color and source_color and title_color.lower() != str(source_color).lower())
        product_reviews = reviews_by_product.get(pid, [])
        ratings = [r["rating"] for r in product_reviews if isinstance(r.get("rating"), int)]

        record = {
            "product_id": pid,
            "name": name,
            "handle": product.get("handle"),
            "url": product.get("url"),
            "brand": product.get("brand", "Tones Fashion"),
            "category": product.get("category"),
            "product_type": raw_types.get(pid),
            "collections": product.get("collections", []),
            "description": description,
            "images": product.get("images", []),
            "price": indexed.get("price", product.get("product_level_price")),
            "compare_at_price": indexed.get("compare_at_price"),
            "currency": indexed.get("currency", product.get("currency", "INR")),
            "color": source_color,
            "name_color": title_color,
            "color_conflict": color_conflict,
            "fit": indexed.get("fit"),
            "fabric": indexed.get("fabric"),
            "sizes": indexed.get("sizes", []),
            "in_stock_sizes": indexed.get("in_stock_sizes", []),
            "variants": indexed.get("variants", product.get("variants", [])),
            "special_conditions": product.get("special_conditions", []),
            "customer_facing_notes": product.get("customer_facing_notes", []),
            "review_summary": {
                "review_count": len(product_reviews),
                "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            },
            "reviews": product_reviews,
            "source": product.get("source", {}),
            "validation": product.get("validation", {}),
        }
        enriched.append(record)

        searchable = " | ".join([
            name, str(record.get("category") or ""), str(record.get("color") or ""),
            str(record.get("fit") or ""), str(record.get("fabric") or ""), description,
            " ".join(str(c.get("collection_url", "")) if isinstance(c, dict) else str(c) for c in record.get("collections", [])),
        ])
        documents.append({
            "doc_id": f"PRODUCT::{pid}",
            "doc_type": "product",
            "entity_id": pid,
            "title": name,
            "text": searchable,
            "status": "VERIFIED_SNAPSHOT",
            "source_url": product.get("url"),
        })

        for review in product_reviews:
            documents.append({
                "doc_id": f"REVIEW::{review['review_id']}",
                "doc_type": "review",
                "entity_id": pid,
                "title": f"Review of {name}",
                "text": f"{name} {review.get('author','')} {review.get('rating','')} stars {review.get('body','')}",
                "review": review,
                "status": "VERIFIED_FROM_SAVED_PAGE",
                "source_url": product.get("url"),
            })

    # Expand business knowledge only with claims already supported by official records.
    extra = [
        {
            "knowledge_id": "TONES-KB-BRAND-002",
            "domain": "business",
            "topic": "brand_differentiation",
            "title": "Why choose TONES Fashion / brand positioning",
            "facts": [
                "TONES says it focuses on clothing, experiences, style and individuality.",
                "TONES says its pieces are designed to blend comfort, quality and timeless appeal.",
                "The TONES homepage describes its standard around carefully sourced fabric, attention to construction, comfort, varied fits, consideration of Indian men, hand checking before shipment, and durability.",
            ],
            "source_url": "https://www.tonesfashion.com/",
            "source_type": "official_homepage_and_about",
            "status": "VERIFIED_WITH_LIMITATION",
            "collected_at": "2026-10-06",
        },
        {
            "knowledge_id": "TONES-KB-PROMO-002",
            "domain": "business",
            "topic": "current_promotions",
            "title": "Current TONES homepage promotions",
            "facts": [
                "The homepage currently displays code TFV10 for 10% off.",
                "The homepage currently displays code TFV25 for 25% off with a stated minimum order of ₹2,000.",
                "The homepage currently displays code TONESCLAN750 for ₹750 off with a stated minimum order of ₹3,000.",
                "Promotions are temporary/current and can change.",
            ],
            "source_url": "https://www.tonesfashion.com/",
            "source_type": "official_homepage",
            "status": "TEMPORARY/CURRENT",
            "collected_at": "2026-10-06",
        },
        {
            "knowledge_id": "TONES-KB-FINANCE-001",
            "domain": "business",
            "topic": "financial_information",
            "title": "Financial information availability",
            "facts": [
                "The current TONES public knowledge snapshot does not contain a verified figure for overall company profit or revenue.",
                "The assistant must not estimate, infer or invent TONES Fashion profit or revenue figures.",
            ],
            "source_url": "https://www.tonesfashion.com/",
            "source_type": "public_information_boundary",
            "status": "VERIFIED_WITH_LIMITATION",
            "collected_at": "2026-10-06",
        },
        {
            "knowledge_id": "TONES-KB-OWNERSHIP-001",
            "domain": "business",
            "topic": "ownership",
            "title": "Ownership information availability",
            "facts": [
                "The current public TONES knowledge snapshot does not contain a verified owner/founder identity.",
                "The assistant must not guess or invent an owner name.",
            ],
            "source_url": "https://www.tonesfashion.com/pages/about",
            "source_type": "public_information_boundary",
            "status": "VERIFIED_WITH_LIMITATION",
            "collected_at": "2026-10-06",
        },
    ]
    known = {r["knowledge_id"] for r in business}
    for item in extra:
        if item["knowledge_id"] not in known:
            business.append(item)

    for record in business:
        text = " ".join([
            str(record.get("title", "")), str(record.get("topic", "")),
            str(record.get("domain", "")), " ".join(record.get("facts", [])),
        ])
        documents.append({
            "doc_id": f"BUSINESS::{record['knowledge_id']}",
            "doc_type": "business",
            "entity_id": record["knowledge_id"],
            "title": record.get("title"),
            "text": text,
            "business": record,
            "status": record.get("status"),
            "source_url": record.get("source_url"),
        })

    (CANONICAL / "products_enriched.json").write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    (CANONICAL / "business_knowledge_v2.json").write_text(json.dumps(business, indent=2, ensure_ascii=False), encoding="utf-8")
    with (RAG / "knowledge_documents.jsonl").open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    manifest = {
        "products": len(enriched),
        "reviews": len(reviews),
        "products_with_reviews": sum(1 for p in enriched if p["reviews"]),
        "business_records": len(business),
        "documents": len(documents),
        "snapshot_source": "TONES official site pages saved in 01_RAW_DATA",
        "generated_on": "2026-10-06",
    }
    (RAG / "knowledge_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
