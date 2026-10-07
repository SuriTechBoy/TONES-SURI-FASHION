import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PAGE_1 = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
    / "TONES-COL-0080.html"
)

PAGE_2 = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
    / "TONES-COL-0080-page-2.html"
)


def extract_products(path):

    html = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    match = re.search(
        r'window\.vtlsLiquidData\.collectionProducts\s*='
        r'\s*(\{.*?\})\s*;',
        html,
        re.I | re.S
    )

    if not match:
        return set()

    data = json.loads(match.group(1))

    return set(data.keys())


page1 = extract_products(PAGE_1)
page2 = extract_products(PAGE_2)

print("THE ONE COLLECTION PAGINATION")
print("=" * 60)

print("Page 1 products:", len(page1))
print("Page 2 products:", len(page2))
print("Combined products:", len(page1 | page2))
print("Overlap:", len(page1 & page2))

print()

print("PRODUCTS ONLY ON PAGE 1:", len(page1 - page2))
print("PRODUCTS ONLY ON PAGE 2:", len(page2 - page1))

print()

print("EXPECTED TOTAL: 68")
print("ACTUAL TOTAL:", len(page1 | page2))

print()

if len(page1 & page2) == 0 and len(page1 | page2) == 68:
    print("VALIDATION: SUCCESS")
    print("Page 1 + Page 2 contain 68 unique products.")
else:
    print("VALIDATION: NEEDS INVESTIGATION")