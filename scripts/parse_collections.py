import csv
import re
from pathlib import Path
from html import unescape

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "01_RAW_DATA" / "collections_html"
OUTPUT_DIR = BASE_DIR / "03_STRUCTURED"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "collection_products.csv"


def clean_text(text):
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


rows = []

html_files = sorted(INPUT_DIR.glob("*.html"))

print(f"Collection HTML files found: {len(html_files)}")
print()

for index, html_file in enumerate(html_files, start=1):

    print(f"[{index}/{len(html_files)}] Parsing {html_file.name}")

    html = html_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    collection_id = html_file.stem

    # Find product-card blocks
    product_blocks = re.findall(
        r'<product-card.*?</product-card>',
        html,
        flags=re.I | re.S
    )

    # Fallback for themes where product-card is not a custom element
    if not product_blocks:
        product_blocks = re.findall(
            r'<li[^>]*class="[^"]*columns[^"]*"[^>]*>.*?</li>',
            html,
            flags=re.I | re.S
        )

    seen_urls = set()

    for block in product_blocks:

        # Product URL
        url_match = re.search(
    r'href=["\'](?:https://www\.tonesfashion\.com)?'
    r'(/collections/[^"\']+/products/[^"\']+|/products/[^"\']+)',
    block,
    flags=re.I
)

        if not url_match:
            continue

        product_path = url_match.group(1)

        if product_path in seen_urls:
            continue

        seen_urls.add(product_path)

        product_url = (
            "https://www.tonesfashion.com"
            + product_path
        )

        # Product title
        title_match = re.search(
            r'title=["\']([^"\']+)["\']',
            block,
            flags=re.I
        )

        title = clean_text(
            title_match.group(1)
        ) if title_match else ""

        # Product card title
        card_title_match = re.search(
            r'class=["\'][^"\']*product-card-title[^"\']*["\'][^>]*>'
            r'(.*?)</',
            block,
            flags=re.I | re.S
        )

        if card_title_match:
            card_title = clean_text(
                card_title_match.group(1)
            )

            if card_title:
                title = card_title

        # Price
        price_match = re.search(
            r'(?:Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)',
            block,
            flags=re.I
        )

        price = (
            price_match.group(1).replace(",", "")
            if price_match
            else ""
        )

        rows.append({
            "collection_id": collection_id,
            "product_url": product_url,
            "product_handle": product_path.split("/")[-1],
            "product_title": title,
            "price": price,
            "source_file": str(
                html_file.relative_to(BASE_DIR)
            )
        })


# Write structured CSV
fieldnames = [
    "collection_id",
    "product_url",
    "product_handle",
    "product_title",
    "price",
    "source_file"
]

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


unique_products = len(
    set(row["product_url"] for row in rows)
)

print()
print("COLLECTION PARSING COMPLETE")
print("----------------------------")
print(f"Collection files parsed: {len(html_files)}")
print(f"Collection-product records: {len(rows)}")
print(f"Unique product URLs found: {unique_products}")
print(f"Output: {OUTPUT_FILE}")