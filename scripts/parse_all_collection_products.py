import csv
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
)

OUTPUT_DIR = (
    BASE_DIR
    / "03_STRUCTURED"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "verified_collection_products.csv"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


rows = []
failed = []


for index, html_file in enumerate(
    sorted(INPUT_DIR.glob("*.html")),
    start=1
):

    print(
        f"[{index}/{len(list(INPUT_DIR.glob('*.html')))}] "
        f"Parsing {html_file.name}"
    )

    html = html_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    match = re.search(
        r'window\.vtlsLiquidData\.collectionProducts\s*=\s*'
        r'(\{.*?\})\s*;',
        html,
        re.I | re.S
    )

    if not match:
        failed.append({
            "collection_id": html_file.stem,
            "reason": "collectionProducts object not found"
        })
        continue

    try:
        collection_products = json.loads(
            match.group(1)
        )

    except json.JSONDecodeError as error:

        failed.append({
            "collection_id": html_file.stem,
            "reason": f"JSON parse error: {error}"
        })

        continue


    for handle, data in collection_products.items():

        collection_ids = data.get(
            "collectionIds",
            []
        )

        if not isinstance(collection_ids, list):
            collection_ids = []

        rows.append({
            "source_collection_id": html_file.stem,
            "product_handle": handle,
            "product_id": data.get("id", ""),
            "variant_id": data.get("variantId", ""),
            "collection_ids": "|".join(
                str(x) for x in collection_ids
            )
        })


fieldnames = [
    "source_collection_id",
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
    writer.writerows(rows)


unique_products = len(
    set(
        row["product_handle"]
        for row in rows
    )
)


print()
print("VERIFIED COLLECTION PARSING COMPLETE")
print("--------------------------------------")
print(f"Collection files processed: {len(list(INPUT_DIR.glob('*.html')))}")
print(f"Verified collection-product records: {len(rows)}")
print(f"Unique product handles: {unique_products}")
print(f"Collections with parsing failures: {len(failed)}")
print(f"Output: {OUTPUT_FILE}")


if failed:

    print()
    print("FAILED COLLECTIONS")
    print("------------------")

    for item in failed:
        print(
            item["collection_id"],
            "|",
            item["reason"]
        )