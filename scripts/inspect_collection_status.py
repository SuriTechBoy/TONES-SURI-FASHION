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

print("FILE")
print("----")
print(html_file.name)

print()
print("PAGE TITLE")
print("----------")

title = re.search(
    r"<title[^>]*>(.*?)</title>",
    html,
    re.I | re.S
)

print(
    re.sub(r"\s+", " ", title.group(1)).strip()
    if title
    else "Not found"
)

print()
print("H1 HEADINGS")
print("-----------")

h1s = re.findall(
    r"<h1[^>]*>(.*?)</h1>",
    html,
    re.I | re.S
)

for h1 in h1s[:10]:
    print(
        re.sub(r"<[^>]+>", " ", h1)
        .replace("&amp;", "&")
        .strip()
    )

print()
print("FILTER / PRODUCT COUNT TEXT")
print("----------------------------")

matches = re.findall(
    r".{0,150}(?:filter-count|products-count|products|items).{0,200}",
    html,
    re.I | re.S
)

for item in matches[:20]:
    clean = re.sub(r"\s+", " ", item).strip()
    print(clean)

print()
print("COLLECTION EMPTY PRESENT")
print("------------------------")

print(
    "YES"
    if re.search(r'class=["\'][^"\']*collection-empty', html, re.I)
    else "NO"
)