import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

LOG_FILE = (
    BASE_DIR
    / "01_RAW_DATA"
    / "product_collection_log.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "03_STRUCTURED"
    / "product_reconciliation.csv"
)


target_handles = {
    "beige-flannel-shirt-copy",
    "double-pocket-off-white-shirt",
    "predator-tee-relaxed-fit-white",
    "urban-drfit-green",
}


with LOG_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as file:

    rows = list(
        csv.DictReader(file)
    )


results = []

for row in rows:

    url = row.get("url", "")

    matched_handle = None

    for handle in target_handles:

        if f"/products/{handle}" in url:

            matched_handle = handle
            break

    if matched_handle:

        results.append({
            "product_handle": matched_handle,
            "url": url,
            "status": row.get("status", ""),
            "product_name": row.get(
                "product_name",
                ""
            ),
            "variants": row.get(
                "variants",
                ""
            ),
            "error": row.get(
                "error",
                ""
            )
        })


fieldnames = [
    "product_handle",
    "url",
    "status",
    "product_name",
    "variants",
    "error"
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
    writer.writerows(results)


print()
print("PRODUCT RECONCILIATION")
print("=" * 60)

print(
    "Target products:",
    len(target_handles)
)

print(
    "Products found in collection log:",
    len(results)
)

for row in results:

    print()
    print(
        row["product_handle"],
        "|",
        row["status"],
        "|",
        row["product_name"],
        "|",
        row["error"]
    )

print()
print("Output:", OUTPUT_FILE)