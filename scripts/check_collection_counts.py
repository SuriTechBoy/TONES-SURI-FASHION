import re
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "01_RAW_DATA" / "collections_html"
OUTPUT_FILE = BASE_DIR / "03_STRUCTURED" / "collection_counts.csv"

rows = []

for html_file in sorted(INPUT_DIR.glob("*.html")):

    html = html_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    products_count = ""
    all_products_count = ""
    products_size = ""

    match = re.search(
        r'"productsCount"\s*:\s*(\d+)',
        html,
        re.I
    )

    if match:
        products_count = match.group(1)

    match = re.search(
        r'"allProductsCount"\s*:\s*(\d+)',
        html,
        re.I
    )

    if match:
        all_products_count = match.group(1)

    match = re.search(
        r'"productsSize"\s*:\s*(\d+)',
        html,
        re.I
    )

    if match:
        products_size = match.group(1)

    rows.append({
        "collection_id": html_file.stem,
        "products_count": products_count,
        "all_products_count": all_products_count,
        "products_size": products_size,
        "source_file": str(
            html_file.relative_to(BASE_DIR)
        )
    })


fieldnames = [
    "collection_id",
    "products_count",
    "all_products_count",
    "products_size",
    "source_file"
]

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


nonzero = [
    r for r in rows
    if r["products_count"] not in ("", "0")
]

zero = [
    r for r in rows
    if r["products_count"] == "0"
]

print("COLLECTION COUNT CHECK")
print("----------------------")
print(f"Collections checked: {len(rows)}")
print(f"Collections with products_count > 0: {len(nonzero)}")
print(f"Collections with products_count = 0: {len(zero)}")
print(f"Output: {OUTPUT_FILE}")

print()
print("Collections with products:")
for r in nonzero:
    print(
        r["collection_id"],
        "| products:",
        r["products_count"]
    )