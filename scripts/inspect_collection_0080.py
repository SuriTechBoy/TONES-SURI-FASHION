import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

html_file = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
    / "TONES-COL-0080.html"
)

html = html_file.read_text(
    encoding="utf-8",
    errors="ignore"
)

print("COLLECTION: TONES-COL-0080")
print("=" * 60)

# Expected product count
match = re.search(
    r'"productsCount"\s*:\s*(\d+)',
    html,
    re.I
)

print(
    "productsCount:",
    match.group(1) if match else "NOT FOUND"
)

# collectionProducts
match = re.search(
    r'window\.vtlsLiquidData\.collectionProducts\s*='
    r'\s*(\{.*?\})\s*;',
    html,
    re.I | re.S
)

print(
    "collectionProducts found:",
    bool(match)
)

if match:

    data = json.loads(match.group(1))

    print(
        "collectionProducts records:",
        len(data)
    )

    print()
    print("FIRST 10 HANDLES")
    print("----------------")

    for i, handle in enumerate(data.keys(), start=1):

        print(i, handle)

        if i >= 10:
            break


# Product grid / pagination clues
print()
print("PAGINATION / PRODUCT DATA CLUES")
print("-------------------------------")

patterns = [
    r'"page"\s*:\s*\d+',
    r'"pages"\s*:\s*\d+',
    r'"pageSize"\s*:\s*\d+',
    r'"limit"\s*:\s*\d+',
    r'"productsSize"\s*:\s*\d+',
    r'paginate',
]

for pattern in patterns:

    matches = re.findall(
        pattern,
        html,
        re.I
    )

    print(
        pattern,
        "=>",
        len(matches),
        matches[:10]
    )


print()
print("USEFUL COLLECTION DATA CONTEXT")
print("=" * 70)

for keyword in [
    '"productsSize"',
    '"productsCount"',
    'collectionProducts'
]:

    print()
    print("KEYWORD:", keyword)
    print("-" * 70)

    match = re.search(
        re.escape(keyword),
        html,
        re.I
    )

    if match:

        start = max(
            0,
            match.start() - 1500
        )

        end = min(
            len(html),
            match.end() + 3000
        )

        print(
            html[start:end]
        )

    else:

        print("NOT FOUND")


print()
print("Done.")