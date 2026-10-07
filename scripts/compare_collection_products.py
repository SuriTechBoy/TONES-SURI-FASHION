import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
COLLECTION_DIR = BASE_DIR / "01_RAW_DATA" / "collections_html"

files = [
    "TONES-COL-0001.html",
    "TONES-COL-0002.html",
]

product_sets = {}

for filename in files:
    path = COLLECTION_DIR / filename
    html = path.read_text(encoding="utf-8", errors="ignore")

    products = set(
        re.findall(
            r'/collections/[^/]+/products/([^?"\' ]+)',
            html,
            re.I
        )
    )

    product_sets[filename] = products

    print(f"{filename}")
    print(f"Unique products: {len(products)}")
    print()

a = product_sets[files[0]]
b = product_sets[files[1]]

print("COMPARISON")
print("----------")
print(f"Only in {files[0]}: {len(a - b)}")
print(f"Only in {files[1]}: {len(b - a)}")
print(f"Common to both: {len(a & b)}")

print()
print("Only in collection 0001:")
for product in sorted(a - b):
    print(" ", product)

print()
print("Only in collection 0002:")
for product in sorted(b - a):
    print(" ", product)