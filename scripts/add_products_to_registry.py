import csv
from pathlib import Path

# ============================================================
# TONES FASHION - ADD PRODUCTS TO MASTER URL REGISTRY
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCT_FILE = (
    PROJECT_ROOT
    / "01_RAW_DATA"
    / "extracted"
    / "validated_product_urls.csv"
)

MASTER_FILE = (
    PROJECT_ROOT
    / "00_MASTER"
    / "tones_sources.csv"
)

BACKUP_FILE = (
    PROJECT_ROOT
    / "00_MASTER"
    / "tones_sources_backup_before_products.csv"
)

# Exact columns required by tones_sources.csv
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

# ============================================================
# 1. READ VALIDATED PRODUCT URLS
# ============================================================

with open(PRODUCT_FILE, "r", encoding="utf-8-sig", newline="") as file:
    product_reader = csv.DictReader(file)
    products = list(product_reader)

print("=" * 60)
print("TONES MASTER URL REGISTRY UPDATE")
print("=" * 60)
print(f"Validated products read: {len(products)}")

# ============================================================
# 2. READ EXISTING MASTER REGISTRY
# ============================================================

with open(MASTER_FILE, "r", encoding="utf-8-sig", newline="") as file:
    master_reader = csv.DictReader(file)

    master_rows = []

    for row in master_reader:
        # Keep only the required fields
        clean_row = {
            column: row.get(column, "")
            for column in FIELDNAMES
        }

        master_rows.append(clean_row)

print(f"Existing registry rows:  {len(master_rows)}")

# ============================================================
# 3. CREATE BACKUP
# ============================================================

with open(
    BACKUP_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=FIELDNAMES
    )

    writer.writeheader()
    writer.writerows(master_rows)

print("Backup created successfully.")

# ============================================================
# 4. FIND EXISTING URLS
# ============================================================

existing_urls = {
    row["url"].strip()
    for row in master_rows
    if row["url"].strip()
}

# ============================================================
# 5. ADD VALIDATED PRODUCTS
# ============================================================

added_count = 0
skipped_count = 0

for product in products:

    url = product.get("url", "").strip()

    if not url:
        continue

    if url in existing_urls:
        skipped_count += 1
        continue

    product_id = product.get(
        "url_id",
        f"TONES-PROD-URL-{added_count + 1:04d}"
    )

    new_row = {
        "url_id": product_id,
        "url": url,
        "page_type": "PRODUCT",
        "category": "Product",
        "title": "",
        "priority": "HIGH",
        "discovered_by": "Sitemap",
        "collection_status": "NOT_COLLECTED",
        "verification_status": "NOT_VERIFIED",
        "collected_at": "",
        "notes": "Product URL discovered from official Shopify product sitemap",
    }

    master_rows.append(new_row)
    existing_urls.add(url)

    added_count += 1

# ============================================================
# 6. SAVE UPDATED MASTER REGISTRY
# ============================================================

with open(
    MASTER_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=FIELDNAMES
    )

    writer.writeheader()
    writer.writerows(master_rows)

# ============================================================
# 7. FINAL RESULTS
# ============================================================

print()
print("=" * 60)
print("UPDATE COMPLETE")
print("=" * 60)
print(f"Validated products read: {len(products)}")
print(f"Products added:          {added_count}")
print(f"Already existed/skipped: {skipped_count}")
print(f"Total registry URLs:     {len(master_rows)}")
print()
print(f"Master registry:")
print(MASTER_FILE)
print()
print(f"Backup:")
print(BACKUP_FILE)
print("=" * 60)