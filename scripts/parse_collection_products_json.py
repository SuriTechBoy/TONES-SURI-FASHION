import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

HTML_FILE = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
    / "TONES-COL-0054.html"
)

html = HTML_FILE.read_text(
    encoding="utf-8",
    errors="ignore"
)

pattern = (
    r'window\.vtlsLiquidData\.collectionProducts\s*=\s*'
    r'(\{.*?\})\s*;'
)

match = re.search(
    pattern,
    html,
    re.I | re.S
)

print("Collection file:", HTML_FILE.name)
print("collectionProducts found:", bool(match))

if not match:
    print("ERROR: collectionProducts object not found")
    exit()

raw_json = match.group(1)

print("Extracted characters:", len(raw_json))

try:
    collection_products = json.loads(raw_json)

except json.JSONDecodeError as e:
    print("JSON parsing failed:")
    print(e)
    exit()

print("JSON parsing: SUCCESS")
print("Products found:", len(collection_products))

print()
print("FIRST 10 PRODUCTS")
print("-----------------")

for index, (handle, data) in enumerate(
    collection_products.items(),
    start=1
):

    print(
        index,
        "|",
        handle,
        "| ID:",
        data.get("id"),
        "| Variant:",
        data.get("variantId"),
        "| Collection IDs:",
        data.get("collectionIds")
    )

    if index >= 10:
        break