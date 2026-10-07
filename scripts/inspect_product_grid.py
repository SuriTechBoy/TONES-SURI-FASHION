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

match = re.search(
    r'<ul[^>]*id=["\']product-grid["\'][^>]*>(.*?)</ul>',
    html,
    re.I | re.S
)

print("Product-grid found:", bool(match))

if match:
    grid = match.group(1)

    print("Product-grid size:", len(grid))
    print()
    print("Product-card count:",
          len(re.findall(r"<product-card", grid, re.I)))

    print()
    print("Product URL count:",
          len(re.findall(
              r'/collections/[^/]+/products/[^?"\' ]+',
              grid,
              re.I
          )))

    print()
    print("FIRST 5000 CHARACTERS OF PRODUCT GRID")
    print("---------------------------------------")
    print(grid[:5000])

else:
    print("PRODUCT GRID NOT FOUND")