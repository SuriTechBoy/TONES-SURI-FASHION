import re
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

print("COLLECTION PAGINATION CHECK")
print("=" * 70)

patterns = [
    r'href=["\']([^"\']*\?page=\d+[^"\']*)["\']',
    r'href=["\']([^"\']*/collections/[^"\']*\?page=\d+[^"\']*)["\']',
]

found = set()

for pattern in patterns:

    matches = re.findall(
        pattern,
        html,
        re.I
    )

    for url in matches:
        found.add(url)

print("Pagination URLs found:", len(found))
print()

for url in sorted(found):
    print(url)

print()
print("=" * 70)
print("PAGINATION TEXT")
print("=" * 70)

matches = re.findall(
    r'.{0,300}(?:pagination|next|load more|show more).{0,500}',
    html,
    re.I | re.S
)

for item in matches[:20]:

    item = re.sub(
        r'\s+',
        ' ',
        item
    ).strip()

    print(item)
    print("-" * 70)