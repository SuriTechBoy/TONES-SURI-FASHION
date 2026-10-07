import csv
import shutil
from pathlib import Path

REGISTRY_FILE = Path("00_MASTER/tones_sources.csv")
BACKUP_FILE = Path("00_MASTER/tones_sources_backup_before_pages.csv")
PAGE_FILE = Path("01_RAW_DATA/extracted/validated_page_urls.csv")

FIELDNAMES = [
    "url_id",
    "url",
    "page_type",
    "category",
    "title",
    "priority",
    "discovered_by",
    "collection_status",
    "verification_status",
    "collected_at",
    "notes",
]

# 1. Create backup
shutil.copy2(REGISTRY_FILE, BACKUP_FILE)

# 2. Read existing registry
with open(
    REGISTRY_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    reader = csv.DictReader(f)

    existing_rows = []

    for row in reader:
        existing_rows.append({
            field: row.get(field, "").strip()
            for field in FIELDNAMES
        })

existing_urls = {
    row["url"]
    for row in existing_rows
    if row["url"]
}

# 3. Read validated pages
with open(
    PAGE_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    reader = csv.DictReader(f)
    page_rows = list(reader)

# 4. Add pages
added = 0
skipped = 0

for row in page_rows:

    url = row["url"].strip()

    if not url:
        continue

    if url in existing_urls:
        skipped += 1
        continue

    existing_rows.append({
        "url_id": row.get("url_id", ""),
        "url": url,
        "page_type": "PAGE",
        "category": "Information Page",
        "title": "",
        "priority": "HIGH",
        "discovered_by": "Sitemap",
        "collection_status": "NOT_COLLECTED",
        "verification_status": "NOT_VERIFIED",
        "collected_at": "",
        "notes": "Page URL discovered from official Shopify pages sitemap",
    })

    existing_urls.add(url)
    added += 1

# 5. Write registry
with open(
    REGISTRY_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=FIELDNAMES
    )

    writer.writeheader()
    writer.writerows(existing_rows)

# 6. Summary
print()
print("TONES MASTER URL REGISTRY — PAGE UPDATE")
print("========================================")
print("Validated pages read:", len(page_rows))
print("Pages added:", added)
print("Already existed/skipped:", skipped)
print("Total registry URLs:", len(existing_rows))
print()
print("Backup created:")
print(BACKUP_FILE)
print()
print("Registry updated:")
print(REGISTRY_FILE)