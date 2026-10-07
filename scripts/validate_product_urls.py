import csv
from pathlib import Path
from urllib.parse import urlparse

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "01_RAW_DATA"
    / "extracted"
    / "product_urls.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "01_RAW_DATA"
    / "extracted"
    / "validated_product_urls.csv"
)

INVALID_FILE = (
    PROJECT_ROOT
    / "01_RAW_DATA"
    / "extracted"
    / "invalid_product_urls.csv"
)

# Read extracted product URLs
with open(INPUT_FILE, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    rows = list(reader)

valid_urls = []
invalid_urls = []
seen_urls = set()

for row in rows:
    url = row["url"].strip()

    # Check empty URL
    if not url:
        row["reason"] = "EMPTY_URL"
        invalid_urls.append(row)
        continue

    # Check URL format
    parsed = urlparse(url)

    if parsed.scheme != "https":
        row["reason"] = "NOT_HTTPS"
        invalid_urls.append(row)
        continue

    # Check correct TONES domain
    if parsed.netloc != "www.tonesfashion.com":
        row["reason"] = "WRONG_DOMAIN"
        invalid_urls.append(row)
        continue

    # Check product path
    if not parsed.path.startswith("/products/"):
        row["reason"] = "NOT_PRODUCT_URL"
        invalid_urls.append(row)
        continue

    # Check duplicate
    if url in seen_urls:
        row["reason"] = "DUPLICATE"
        invalid_urls.append(row)
        continue

    seen_urls.add(url)
    valid_urls.append(row)

# Re-number valid URLs
for number, row in enumerate(valid_urls, start=1):
    row["url_id"] = f"TONES-PROD-URL-{number:04d}"

# Save validated URLs
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["url_id", "url", "page_type", "source"]
    )

    writer.writeheader()

    for row in valid_urls:
        writer.writerow({
            "url_id": row["url_id"],
            "url": row["url"],
            "page_type": row["page_type"],
            "source": row["source"]
        })

# Save invalid URLs
with open(INVALID_FILE, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "url_id",
            "url",
            "page_type",
            "source",
            "reason"
        ]
    )

    writer.writeheader()

    for row in invalid_urls:
        writer.writerow(row)

# Results
print("=" * 60)
print("TONES PRODUCT URL VALIDATION")
print("=" * 60)
print(f"URLs read:        {len(rows)}")
print(f"Valid URLs:       {len(valid_urls)}")
print(f"Invalid/Duplicate:{len(invalid_urls)}")
print(f"Unique URLs:      {len(seen_urls)}")
print()
print(f"Validated file:   {OUTPUT_FILE}")
print(f"Invalid file:     {INVALID_FILE}")
print("=" * 60)