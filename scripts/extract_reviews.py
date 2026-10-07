"""Extract product-specific Judge.me reviews from the saved TONES product HTML snapshot."""
from __future__ import annotations

import json
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "01_RAW_DATA" / "products_html"
PRODUCTS_FILE = BASE_DIR / "05_CANONICAL" / "products_canonical_with_collections.json"
OUT_FILE = BASE_DIR / "05_CANONICAL" / "reviews_canonical.json"
SUMMARY_FILE = BASE_DIR / "05_CANONICAL" / "product_review_summary.json"


def main() -> None:
    products = {p["product_id"]: p for p in json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))}
    rows = []
    summary = {}

    for html_path in sorted(RAW_DIR.glob("*.html")):
        product_id = html_path.stem
        product = products.get(product_id)
        if not product:
            continue

        soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        reviews = []
        for node in soup.select(".jdgm-rev[data-review-id]"):
            rating_node = node.select_one(".jdgm-rev__rating")
            author_node = node.select_one(".jdgm-rev__author")
            body_node = node.select_one(".jdgm-rev__body")
            time_node = node.select_one(".jdgm-rev__timestamp")
            rating = None
            if rating_node and rating_node.get("data-score"):
                try:
                    rating = int(rating_node["data-score"])
                except ValueError:
                    pass

            review = {
                "review_id": node.get("data-review-id"),
                "product_id": product_id,
                "product_name": product.get("name"),
                "product_url": product.get("url"),
                "rating": rating,
                "author": author_node.get_text(" ", strip=True) if author_node else "Anonymous",
                "body": body_node.get_text(" ", strip=True) if body_node else "",
                "date": (time_node.get("data-content") or time_node.get("datetime")) if time_node else None,
                "verified_buyer": node.get("data-verified-buyer") == "true",
                "source": "TONES product page / Judge.me",
                "source_url": product.get("url"),
                "validation_status": "VERIFIED_FROM_SAVED_PAGE",
            }
            if review["review_id"] and review["body"]:
                reviews.append(review)
                rows.append(review)

        ratings = [r["rating"] for r in reviews if isinstance(r.get("rating"), int)]
        summary[product_id] = {
            "product_id": product_id,
            "product_name": product.get("name"),
            "review_count": len(reviews),
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "rating_distribution": {str(star): sum(1 for r in reviews if r.get("rating") == star) for star in range(1, 6)},
        }

    OUT_FILE.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(rows)} reviews across {sum(1 for x in summary.values() if x['review_count'])} products")


if __name__ == "__main__":
    main()
