import csv
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

HTML_DIR = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
)

CSV_FILE = (
    BASE_DIR
    / "03_STRUCTURED"
    / "verified_collection_products.csv"
)


# Read verified parsed relationships
with CSV_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as file:

    rows = list(
        csv.DictReader(file)
    )


actual_counts = Counter(
    row["source_collection_id"]
    for row in rows
)


results = []

for html_file in sorted(
    HTML_DIR.glob("*.html")
):

    html = html_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    match = re.search(
        r'"productsCount"\s*:\s*(\d+)',
        html,
        re.I
    )

    expected = (
        int(match.group(1))
        if match
        else None
    )

    actual = actual_counts.get(
        html_file.stem,
        0
    )

    results.append({
        "collection_id": html_file.stem,
        "expected_products": expected,
        "extracted_products": actual,
        "match": (
            expected == actual
            if expected is not None
            else False
        )
    })


matches = [
    r for r in results
    if r["match"]
]

mismatches = [
    r for r in results
    if not r["match"]
]


print()
print("VERIFIED COLLECTION VALIDATION")
print("--------------------------------")
print(f"Collections checked: {len(results)}")
print(f"Count matches: {len(matches)}")
print(f"Count mismatches: {len(mismatches)}")

print()

if mismatches:

    print("MISMATCHES")
    print("----------")

    for row in mismatches:
        print(
            row["collection_id"],
            "| expected:",
            row["expected_products"],
            "| extracted:",
            row["extracted_products"]
        )

else:

    print(
        "SUCCESS: Every collection's "
        "productsCount matches the extracted "
        "collectionProducts records."
    )