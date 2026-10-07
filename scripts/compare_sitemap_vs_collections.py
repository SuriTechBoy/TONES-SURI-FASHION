import csv
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCT_URLS_FILE = (
    BASE_DIR
    / "01_RAW_DATA"
    / "extracted"
    / "validated_product_urls.csv"
)

COLLECTION_PRODUCTS_FILE = (
    BASE_DIR
    / "03_STRUCTURED"
    / "verified_collection_products_all.csv"
)


# Read product sitemap URLs
with PRODUCT_URLS_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as file:

    product_rows = list(
        csv.DictReader(file)
    )


sitemap_handles = set()

for row in product_rows:

    url = row["url"].rstrip("/")

    handle = urlparse(url).path.split(
        "/products/",
        1
    )[-1]

    if handle:
        sitemap_handles.add(handle)


# Read collection products
with COLLECTION_PRODUCTS_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as file:

    collection_rows = list(
        csv.DictReader(file)
    )


collection_handles = set(
    row["product_handle"]
    for row in collection_rows
    if row["product_handle"]
)


missing_from_collections = (
    sitemap_handles - collection_handles
)

only_in_collections = (
    collection_handles - sitemap_handles
)


print()
print("SITEMAP vs COLLECTION PRODUCT RECONCILIATION")
print("=" * 70)

print(
    "Sitemap product handles:",
    len(sitemap_handles)
)

print(
    "Collection product handles:",
    len(collection_handles)
)

print(
    "Missing from collections:",
    len(missing_from_collections)
)

print(
    "Only in collections:",
    len(only_in_collections)
)

print()

print("PRODUCTS IN SITEMAP BUT NOT IN COLLECTIONS")
print("-------------------------------------------")

for handle in sorted(
    missing_from_collections
):

    print(handle)


print()

print("PRODUCTS IN COLLECTIONS BUT NOT IN SITEMAP")
print("-------------------------------------------")

for handle in sorted(
    only_in_collections
):

    print(handle)

print()
print("Done.")