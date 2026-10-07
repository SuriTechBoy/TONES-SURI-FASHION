import csv
import json
import re
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

REGISTRY_FILE = (
    BASE_DIR
    / "00_MASTER"
    / "tones_sources.csv"
)

HTML_DIR = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
)

OUTPUT_FILE = (
    BASE_DIR
    / "03_STRUCTURED"
    / "verified_collection_products_all.csv"
)

SHOPIFY_IP = "23.227.38.32"
DOMAIN = "www.tonesfashion.com"


def download(url, output_file):

    command = [
        "curl.exe",
        "-L",
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

    return result.returncode == 0


def extract_collection_products(html):

    match = re.search(
        r'window\.vtlsLiquidData\.collectionProducts\s*='
        r'\s*(\{.*?\})\s*;',
        html,
        re.I | re.S
    )

    if not match:
        return {}

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def extract_expected_count(html):

    match = re.search(
        r'"productsCount"\s*:\s*(\d+)',
        html,
        re.I
    )

    if match:
        return int(match.group(1))

    return None


# Read collection URLs
with REGISTRY_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as file:

    registry = list(
        csv.DictReader(file)
    )


collections = [
    row
    for row in registry
    if row["page_type"] == "COLLECTION"
]


all_rows = []
collection_results = []


print()
print("AUTOMATED COLLECTION PAGINATION")
print("=" * 70)
print("Collections:", len(collections))
print()


for index, collection in enumerate(
    collections,
    start=1
):

    collection_id = collection["url_id"]
    base_url = collection["url"]

    print(
        f"[{index}/{len(collections)}] "
        f"{collection_id}"
    )

    # --------------------------------------------------
    # PAGE 1
    # --------------------------------------------------

    page1_file = (
        HTML_DIR
        / f"{collection_id}.html"
    )

    if not page1_file.exists():

        print("  Page 1 HTML missing")

        collection_results.append({
            "collection_id": collection_id,
            "expected": None,
            "extracted": 0,
            "status": "MISSING_PAGE_1"
        })

        print()
        continue

    html = page1_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    expected = extract_expected_count(
        html
    )

    products = extract_collection_products(
        html
    )

    print(
        f"  Page 1 products: {len(products)}"
    )

    # Start with page 1 products
    combined = dict(products)

    # --------------------------------------------------
    # ADDITIONAL PAGES
    # --------------------------------------------------

    page_number = 2

    while (
        expected is not None
        and len(combined) < expected
    ):

        page_url = (
            base_url
            + ("&" if "?" in base_url else "?")
            + f"page={page_number}"
        )

        page_file = (
            HTML_DIR
            / f"{collection_id}-page-{page_number}.html"
        )

        print(
            f"  Checking page {page_number}"
        )

        # Download page if not already available
        if not page_file.exists():

            print(
                f"  Downloading page {page_number}"
            )

            success = download(
                page_url,
                page_file
            )

            if not success:

                print(
                    f"  FAILED page {page_number}"
                )

                break

        # Read page
        page_html = page_file.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        # Extract products
        page_products = extract_collection_products(
            page_html
        )

        print(
            f"  Page {page_number} products: "
            f"{len(page_products)}"
        )

        # No products = stop
        if not page_products:

            print(
                "  No additional products found."
            )

            break

        # Count before adding
        before = len(combined)

        # Add products
        for handle, data in page_products.items():

            combined[handle] = data

        # Count newly added products
        added = len(combined) - before

        print(
            f"  New unique products: {added}"
        )

        # If page contains only duplicates,
        # stop to prevent an endless loop.
        if added == 0:

            print(
                "  No new unique products. Stopping."
            )

            break

        page_number += 1

    # --------------------------------------------------
    # SAVE COLLECTION-PRODUCT RELATIONSHIPS
    # --------------------------------------------------

    for handle, data in combined.items():

        collection_ids = data.get(
            "collectionIds",
            []
        )

        if not isinstance(
            collection_ids,
            list
        ):

            collection_ids = []

        all_rows.append({
            "collection_id": collection_id,
            "collection_url": base_url,
            "product_handle": handle,
            "product_id": data.get(
                "id",
                ""
            ),
            "variant_id": data.get(
                "variantId",
                ""
            ),
            "collection_ids": "|".join(
                str(x)
                for x in collection_ids
            )
        })

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if expected is None:

        status = "NO_EXPECTED_COUNT"

    elif expected == len(combined):

        status = "MATCH"

    else:

        status = "MISMATCH"

    collection_results.append({
        "collection_id": collection_id,
        "expected": expected,
        "extracted": len(combined),
        "status": status
    })

    print(
        f"  Expected: {expected}"
    )

    print(
        f"  Combined: {len(combined)}"
    )

    print(
        f"  Status: {status}"
    )

    print()


# ------------------------------------------------------
# WRITE FINAL CSV
# ------------------------------------------------------

fieldnames = [
    "collection_id",
    "collection_url",
    "product_handle",
    "product_id",
    "variant_id",
    "collection_ids"
]


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(all_rows)


# ------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------

matches = [
    row
    for row in collection_results
    if row["status"] == "MATCH"
]

mismatches = [
    row
    for row in collection_results
    if row["status"] == "MISMATCH"
]

missing = [
    row
    for row in collection_results
    if row["status"] == "MISSING_PAGE_1"
]


print()
print("=" * 70)
print("AUTOMATED PAGINATION COMPLETE")
print("=" * 70)

print(
    "Collections processed:",
    len(collection_results)
)

print(
    "Collections matching:",
    len(matches)
)

print(
    "Collections needing review:",
    len(mismatches)
)

print(
    "Collections missing page 1:",
    len(missing)
)

print(
    "Total collection-product records:",
    len(all_rows)
)

print(
    "Output:",
    OUTPUT_FILE
)


if mismatches:

    print()
    print("COLLECTIONS NEEDING REVIEW")
    print("--------------------------")

    for row in mismatches:

        print(
            row["collection_id"],
            "| expected:",
            row["expected"],
            "| extracted:",
            row["extracted"]
        )