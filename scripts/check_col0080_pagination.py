import re
from pathlib import Path

file = Path(
    "01_RAW_DATA/collections_html/TONES-COL-0080.html"
)

html = file.read_text(
    encoding="utf-8",
    errors="ignore"
)

print("COLLECTION: TONES-COL-0080")
print("=" * 60)

matches = re.findall(
    r'href=["\']([^"\']*\?page=\d+[^"\']*)["\']',
    html,
    re.I
)

matches = sorted(set(matches))

print("Detected pagination links:", len(matches))
print()

for url in matches:
    print(url)

print()
print("Done.")