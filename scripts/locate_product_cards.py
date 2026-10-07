import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

html_file = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
    / "TONES-COL-0001.html"
)

html = html_file.read_text(
    encoding="utf-8",
    errors="ignore"
)

match = re.search(r"<product-card", html, re.I)

if not match:
    print("No product-card found")
    exit()

start = match.start()

# Find the nearest section/div/ul opening tags before the product card
before = html[:start]

section_positions = [
    (m.start(), m.group(0))
    for m in re.finditer(
        r"<(?:section|div|ul|li)[^>]*>",
        before,
        re.I
    )
]

print("First product-card position:", start)
print()
print("=" * 70)
print("NEAREST CONTAINER TAGS BEFORE PRODUCT CARD")
print("=" * 70)

for position, tag in section_positions[-15:]:
    print(f"{position}: {tag}")

print()
print("=" * 70)
print("HTML AROUND PRODUCT CARD")
print("=" * 70)

print(
    html[
        max(0, start - 1500):
        start + 1000
    ]
)