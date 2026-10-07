import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

html_file = (
    BASE_DIR
    / "01_RAW_DATA"
    / "collections_html"
    / "TONES-COL-0054.html"
)

html = html_file.read_text(
    encoding="utf-8",
    errors="ignore"
)

print("Collection:", html_file.name)
print()

patterns = [
    r"productsCount",
    r"collectionProducts",
    r"productCount",
    r"productsSize",
]

for pattern in patterns:
    matches = list(re.finditer(pattern, html, re.I))

    print(f"{pattern}: {len(matches)} occurrence(s)")

    for match in matches[:3]:
        start = max(0, match.start() - 300)
        end = min(len(html), match.end() + 700)

        print()
        print(html[start:end])
        print("-" * 60)

print()
print("Done.")