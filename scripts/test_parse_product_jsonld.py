import json
import re
import html
from pathlib import Path


INPUT_FILE = Path(
    "01_RAW_DATA/extracted/test_product.html"
)

OUTPUT_FILE = Path(
    "01_RAW_DATA/extracted/test_product_parsed.json"
)


def extract_jsonld(html_text):
    pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'

    blocks = re.findall(
        pattern,
        html_text,
        flags=re.IGNORECASE | re.DOTALL
    )

    results = []

    for block in blocks:
        try:
            data = json.loads(block.strip())
            results.append(data)
        except json.JSONDecodeError:
            pass

    return results


def collect_product_objects(data):
    products = []

    if isinstance(data, dict):

        data_type = data.get("@type", "")

        if isinstance(data_type, list):
            is_product = (
                "Product" in data_type
                or "ProductGroup" in data_type
            )
        else:
            is_product = (
                data_type == "Product"
                or data_type == "ProductGroup"
            )

        if is_product:
            products.append(data)

        # Handle @graph
        if "@graph" in data:
            products.extend(
                collect_product_objects(data["@graph"])
            )

    elif isinstance(data, list):

        for item in data:
            products.extend(
                collect_product_objects(item)
            )

    return products


def clean_text(value):
    if not value:
        return ""

    return html.unescape(
        str(value)
    ).strip()


def extract_variant(variant):
    offer = variant.get("offers", {})

    if isinstance(offer, list):
        offer = offer[0] if offer else {}

    return {
        "name": clean_text(variant.get("name")),
        "sku": clean_text(variant.get("sku")),
        "url": variant.get("url", ""),
        "price": offer.get("price"),
        "currency": offer.get("priceCurrency"),
        "availability": offer.get("availability"),
        "image": variant.get("image", "")
    }


# --------------------------------------------------
# Read HTML
# --------------------------------------------------

html_text = INPUT_FILE.read_text(
    encoding="utf-8",
    errors="ignore"
)

jsonld_blocks = extract_jsonld(html_text)

print("JSON-LD blocks found:", len(jsonld_blocks))


# --------------------------------------------------
# Find product object
# --------------------------------------------------

product_objects = []

for block in jsonld_blocks:
    product_objects.extend(
        collect_product_objects(block)
    )

print("Product objects found:", len(product_objects))

if not product_objects:
    raise SystemExit(
        "No Product/ProductGroup JSON-LD found."
    )


# Prefer object containing variants
product = next(
    (
        p for p in product_objects
        if p.get("hasVariant")
    ),
    product_objects[0]
)


# --------------------------------------------------
# Basic product information
# --------------------------------------------------

brand = product.get("brand", {})

if isinstance(brand, dict):
    brand_name = brand.get("name", "")
else:
    brand_name = str(brand)


aggregate_rating = product.get(
    "aggregateRating",
    {}
)

parsed_product = {
    "name": clean_text(
        product.get("name")
    ),

    "sku": clean_text(
        product.get("sku")
    ),

    "url": product.get(
        "url",
        ""
    ),

    "description": clean_text(
        product.get("description")
    ),

    "brand": clean_text(
        brand_name
    ),

    "category": clean_text(
        product.get("category")
    ),

    "image": product.get(
        "image",
        []
    ),

    "aggregate_rating": {
        "rating_value": aggregate_rating.get(
            "ratingValue"
        ),
        "review_count": aggregate_rating.get(
            "reviewCount"
        )
    },

    "variants": []
}


# --------------------------------------------------
# Extract variants
# --------------------------------------------------

variants = product.get(
    "hasVariant",
    []
)

if isinstance(variants, dict):
    variants = [variants]

for variant in variants:

    parsed_product["variants"].append(
        extract_variant(variant)
    )


# --------------------------------------------------
# Save
# --------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        parsed_product,
        f,
        indent=2,
        ensure_ascii=False
    )


# --------------------------------------------------
# Summary
# --------------------------------------------------

print()
print("PRODUCT PARSING COMPLETE")
print("========================")
print(
    "Product:",
    parsed_product["name"]
)
print(
    "SKU:",
    parsed_product["sku"]
)
print(
    "Brand:",
    parsed_product["brand"]
)
print(
    "Category:",
    parsed_product["category"]
)
print(
    "Variants:",
    len(parsed_product["variants"])
)
print(
    "Output:",
    OUTPUT_FILE
)