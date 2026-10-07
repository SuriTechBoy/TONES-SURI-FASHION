import xml.etree.ElementTree as ET
import csv
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SITEMAP_FILE = (
    PROJECT_ROOT
    / "01_RAW_DATA"
    / "sitemap"
    / "sitemap_products_1.xml"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "01_RAW_DATA"
    / "extracted"
    / "product_urls.csv"
)

# Read the XML sitemap
tree = ET.parse(SITEMAP_FILE)
root = tree.getroot()

# Sitemap XML namespace
namespace = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}

# Extract product URLs
product_urls = []

for url in root.findall("sm:url", namespace):
    loc = url.find("sm:loc", namespace)

    if loc is not None and loc.text:
        product_url = loc.text.strip()

        if "/products/" in product_url:
            product_urls.append(product_url)

# Remove duplicates while preserving order
product_urls = list(dict.fromkeys(product_urls))

# Create output directory if it doesn't exist
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Save URLs to CSV
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "url_id",
        "url",
        "page_type",
        "source"
    ])

    for number, url in enumerate(product_urls, start=1):
        writer.writerow([
            f"TONES-PROD-URL-{number:04d}",
            url,
            "PRODUCT",
            "Shopify Product Sitemap"
        ])

print("=" * 60)
print("TONES PRODUCT URL EXTRACTION")
print("=" * 60)
print(f"Product URLs found: {len(product_urls)}")
print(f"Output file: {OUTPUT_FILE}")
print("=" * 60)