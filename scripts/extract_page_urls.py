import csv
import xml.etree.ElementTree as ET
from pathlib import Path

SITEMAP_FILE = Path("01_RAW_DATA/sitemap/sitemap_pages_1.xml")
OUTPUT_FILE = Path("01_RAW_DATA/extracted/page_urls.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}

tree = ET.parse(SITEMAP_FILE)
root = tree.getroot()

urls = []

for loc in root.findall(".//sm:loc", NS):
    url = loc.text.strip()

    if "/pages/" in url:
        urls.append(url)

urls = sorted(set(urls))

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "url_id",
        "url",
        "page_type",
        "source"
    ])

    for i, url in enumerate(urls, start=1):
        writer.writerow([
            f"TONES-PAGE-{i:04d}",
            url,
            "PAGE",
            "Sitemap"
        ])

print("Page URLs extracted:", len(urls))
print("Output:", OUTPUT_FILE)