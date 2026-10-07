import csv
from pathlib import Path
from urllib.parse import urlparse

INPUT_FILE = Path("01_RAW_DATA/extracted/blog_urls.csv")
VALID_FILE = Path("01_RAW_DATA/extracted/validated_blog_urls.csv")
INVALID_FILE = Path("01_RAW_DATA/extracted/invalid_blog_urls.csv")

EXPECTED_DOMAIN = "www.tonesfashion.com"

valid_urls = []
invalid_urls = []
seen_urls = set()

with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        url = row["url"].strip()
        reason = ""

        if not url:
            reason = "Empty URL"

        elif url in seen_urls:
            reason = "Duplicate URL"

        else:
            seen_urls.add(url)

            parsed = urlparse(url)

            if parsed.scheme != "https":
                reason = "Not HTTPS"

            elif parsed.netloc != EXPECTED_DOMAIN:
                reason = "Invalid domain"

            elif not parsed.path.startswith("/blogs/"):
                reason = "Not a blog URL"

        if reason:
            invalid_urls.append({
                "url_id": row.get("url_id", ""),
                "url": url,
                "reason": reason
            })
        else:
            valid_urls.append({
                "url_id": row.get("url_id", ""),
                "url": url,
                "page_type": "BLOG",
                "source": "Sitemap"
            })

with open(VALID_FILE, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["url_id", "url", "page_type", "source"]
    )
    writer.writeheader()
    writer.writerows(valid_urls)

with open(INVALID_FILE, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["url_id", "url", "reason"]
    )
    writer.writeheader()
    writer.writerows(invalid_urls)

print("BLOG URL VALIDATION")
print("-------------------")
print("URLs read:", len(valid_urls) + len(invalid_urls))
print("Valid URLs:", len(valid_urls))
print("Invalid/Duplicate:", len(invalid_urls))
print("Unique URLs:", len(seen_urls))
print()
print("Valid file:", VALID_FILE)
print("Invalid file:", INVALID_FILE)