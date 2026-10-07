import csv
import json
import re
import html
import subprocess
from pathlib import Path
from datetime import datetime


# ============================================================
# PATHS
# ============================================================

INPUT_FILE = Path(
    "01_RAW_DATA/extracted/validated_product_urls.csv"
)

HTML_DIR = Path(
    "01_RAW_DATA/products_html"
)

JSON_DIR = Path(
    "01_RAW_DATA/products_json"
)

LOG_FILE = Path(
    "01_RAW_DATA/product_collection_log.csv"
)

HTML_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

SHOPIFY_IP = "23.227.38.32"
DOMAIN = "www.tonesfashion.com"


# ============================================================
# JSON-LD EXTRACTION
# ============================================================

def extract_jsonld(html_text):

    pattern = (
        r'<script[^>]*type=["\']application/ld\+json'
        r'["\'][^>]*>(.*?)</script>'
    )

    blocks = re.findall(
        pattern,
        html_text,
        flags=re.IGNORECASE | re.DOTALL
    )

    results = []

    for block in blocks:

        try:
            data = json.loads(
                html.unescape(block.strip())
            )

            results.append(data)

        except json.JSONDecodeError:
            continue

    return results


# ============================================================
# FIND PRODUCT OBJECTS
# ============================================================

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

        if "@graph" in data:

            products.extend(
                collect_product_objects(
                    data["@graph"]
                )
            )

    elif isinstance(data, list):

        for item in data:

            products.extend(
                collect_product_objects(item)
            )

    return products


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):

    if value is None:
        return ""

    return html.unescape(
        str(value)
    ).strip()


# ============================================================
# EXTRACT OFFER
# ============================================================

def extract_offer(offer):

    if isinstance(offer, list):

        if offer:
            return offer[0]

        return {}

    if isinstance(offer, dict):
        return offer

    return {}


# ============================================================
# EXTRACT VARIANT
# ============================================================

def extract_variant(variant):

    offer = extract_offer(
        variant.get("offers", {})
    )

    return {
        "name": clean_text(
            variant.get("name")
        ),

        "sku": clean_text(
            variant.get("sku")
        ),

        "url": variant.get(
            "url",
            ""
        ),

        "price": offer.get(
            "price"
        ),

        "currency": offer.get(
            "priceCurrency"
        ),

        "availability": offer.get(
            "availability"
        ),

        "image": variant.get(
            "image",
            ""
        )
    }


# ============================================================
# PARSE PRODUCT
# ============================================================

def parse_product(html_text, source_url):

    jsonld_blocks = extract_jsonld(
        html_text
    )

    product_objects = []

    for block in jsonld_blocks:

        product_objects.extend(
            collect_product_objects(block)
        )

    if not product_objects:

        raise ValueError(
            "No Product/ProductGroup JSON-LD found"
        )

    # Prefer ProductGroup containing variants
    product = next(
        (
            p for p in product_objects
            if p.get("hasVariant")
        ),
        product_objects[0]
    )

    brand = product.get(
        "brand",
        {}
    )

    if isinstance(brand, dict):
        brand_name = brand.get(
            "name",
            ""
        )
    else:
        brand_name = str(brand)

    rating = product.get(
        "aggregateRating",
        {}
    )

    variants = product.get(
        "hasVariant",
        []
    )

    if isinstance(variants, dict):
        variants = [variants]

    parsed_variants = []

    for variant in variants:

        if isinstance(variant, dict):

            parsed_variants.append(
                extract_variant(variant)
            )

    return {
        "source_url": source_url,

        "collected_at": datetime.now().isoformat(),

        "name": clean_text(
            product.get("name")
        ),

        "sku": clean_text(
            product.get("sku")
        ),

        "url": product.get(
            "url",
            source_url
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
            "rating_value": rating.get(
                "ratingValue"
            ),

            "review_count": rating.get(
                "reviewCount"
            )
        },

        "variants": parsed_variants,

        "collection_method": "JSON-LD"
    }


# ============================================================
# DOWNLOAD HTML
# ============================================================

def download_product(url, output_file):

    command = [
        "curl.exe",

        "-L",

        "--fail",

        "--silent",

        "--show-error",

        "--resolve",
        f"{DOMAIN}:443:{SHOPIFY_IP}",

        url,

        "-o",
        str(output_file)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        error = result.stderr.strip()

        raise RuntimeError(
            error or
            f"curl failed with code {result.returncode}"
        )


# ============================================================
# LOAD PRODUCT URLS
# ============================================================

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    products = list(reader)


print()
print("TONES PRODUCT COLLECTION")
print("========================")
print("Products to collect:", len(products))
print()


# ============================================================
# COLLECTION LOG
# ============================================================

log_rows = []


# ============================================================
# PROCESS PRODUCTS
# ============================================================

for index, row in enumerate(
    products,
    start=1
):

    url = row["url"].strip()

    url_id = row.get(
        "url_id",
        f"TONES-PROD-{index:04d}"
    )

    print(
        f"[{index}/{len(products)}] {url}"
    )

    html_file = HTML_DIR / (
        f"{url_id}.html"
    )

    json_file = JSON_DIR / (
        f"{url_id}.json"
    )

    try:

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        download_product(
            url,
            html_file
        )

        # ----------------------------------------------------
        # Read HTML
        # ----------------------------------------------------

        html_text = html_file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        # ----------------------------------------------------
        # Parse JSON-LD
        # ----------------------------------------------------

        parsed = parse_product(
            html_text,
            url
        )

        # Add registry information
        parsed["url_id"] = url_id

        # ----------------------------------------------------
        # Save parsed JSON
        # ----------------------------------------------------

        with open(
            json_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                parsed,
                f,
                indent=2,
                ensure_ascii=False
            )

        log_rows.append({
            "url_id": url_id,
            "url": url,
            "status": "SUCCESS",
            "product_name": parsed.get(
                "name",
                ""
            ),
            "variants": len(
                parsed.get(
                    "variants",
                    []
                )
            ),
            "error": ""
        })

        print(
            f"    SUCCESS | "
            f"{parsed.get('name', '')} | "
            f"Variants: "
            f"{len(parsed.get('variants', []))}"
        )

    except Exception as e:

        log_rows.append({
            "url_id": url_id,
            "url": url,
            "status": "FAILED",
            "product_name": "",
            "variants": 0,
            "error": str(e)
        })

        print(
            f"    FAILED | {e}"
        )


# ============================================================
# WRITE COLLECTION LOG
# ============================================================

with open(
    LOG_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "url_id",
            "url",
            "status",
            "product_name",
            "variants",
            "error"
        ]
    )

    writer.writeheader()
    writer.writerows(log_rows)


# ============================================================
# FINAL SUMMARY
# ============================================================

success_count = sum(
    1
    for row in log_rows
    if row["status"] == "SUCCESS"
)

failed_count = sum(
    1
    for row in log_rows
    if row["status"] == "FAILED"
)


print()
print("================================")
print("PRODUCT COLLECTION COMPLETE")
print("================================")
print(
    "Products attempted:",
    len(products)
)

print(
    "Successful:",
    success_count
)

print(
    "Failed:",
    failed_count
)

print()
print(
    "HTML folder:",
    HTML_DIR
)

print(
    "JSON folder:",
    JSON_DIR
)

print(
    "Log file:",
    LOG_FILE
)