import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCT_FILE = (
    BASE_DIR
    / "05_CANONICAL"
    / "products_canonical.json"
)

COLLECTION_FILE = (
    BASE_DIR
    / "03_STRUCTURED"
    / "verified_collection_products_all.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "05_CANONICAL"
    / "products_canonical_with_collections.json"
)


# ---------------------------------------------------------
# Load canonical products
# ---------------------------------------------------------

with PRODUCT_FILE.open(
    encoding="utf-8"
) as f:

    products = json.load(f)


# ---------------------------------------------------------
# Build product → collection mapping
# ---------------------------------------------------------

product_collections = {}

with COLLECTION_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        handle = row.get(
            "product_handle",
            ""
        ).strip()

        collection_id = row.get(
            "collection_id",
            ""
        ).strip()

        collection_url = row.get(
            "collection_url",
            ""
        ).strip()

        if not handle or not collection_id:
            continue

        product_collections.setdefault(
            handle,
            {}
        )

        product_collections[handle][
            collection_id
        ] = collection_url


# ---------------------------------------------------------
# Attach collections to canonical products
# ---------------------------------------------------------

matched = 0
unmatched = 0
total_links = 0


for product in products:

    # Current canonical records may not have handle populated,
    # so derive it from the product URL when necessary.

    handle = product.get(
        "handle",
        ""
    ).strip()

    if not handle:

        url = product.get(
            "url",
            ""
        ).strip()

        if "/products/" in url:

            handle = url.split(
                "/products/",
                1
            )[1].split(
                "?",
                1
            )[0].rstrip("/")


    collection_map = product_collections.get(
        handle,
        {}
    )

    collection_records = []

    for collection_id, collection_url in sorted(
        collection_map.items()
    ):

        collection_records.append({
            "collection_id": collection_id,
            "collection_url": collection_url
        })

    product["collections"] = collection_records

    if collection_records:
        matched += 1
        total_links += len(collection_records)

    else:
        unmatched += 1


# ---------------------------------------------------------
# Save output
# ---------------------------------------------------------

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        products,
        f,
        indent=2,
        ensure_ascii=False
    )


print()
print("PRODUCT → COLLECTION MAPPING")
print("=" * 60)

print(
    "Canonical products:",
    len(products)
)

print(
    "Products with collections:",
    matched
)

print(
    "Products without collections:",
    unmatched
)

print(
    "Collection relationships:",
    total_links
)

print()
print("Output:", OUTPUT_FILE)