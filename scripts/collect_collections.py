import csv
import subprocess
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "01_RAW_DATA" / "extracted" / "validated_collection_urls.csv"
OUTPUT_DIR = BASE_DIR / "01_RAW_DATA" / "collections_html"
LOG_FILE = BASE_DIR / "01_RAW_DATA" / "collection_collection_log.csv"

SHOPIFY_IP = "23.227.38.32"
DOMAIN = "www.tonesfashion.com"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Read validated collection URLs
with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

log_rows = []

for index, row in enumerate(rows, start=1):
    url_id = row["url_id"]
    url = row["url"]

    output_file = OUTPUT_DIR / f"{url_id}.html"

    print(f"[{index}/{len(rows)}] Collecting {url_id}")

    command = [
        "curl.exe",
        "-L",
        "--silent",
        "--show-error",
        "--fail",
        "--resolve",
        f"{DOMAIN}:443:{SHOPIFY_IP}",
        url,
        "-o",
        str(output_file)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and output_file.exists():
        size = output_file.stat().st_size

        log_rows.append({
            "url_id": url_id,
            "url": url,
            "status": "SUCCESS",
            "file": str(output_file.relative_to(BASE_DIR)),
            "size_bytes": size,
            "error": ""
        })

        print(f"  SUCCESS - {size:,} bytes")

    else:
        error = result.stderr.strip()

        if output_file.exists():
            output_file.unlink()

        log_rows.append({
            "url_id": url_id,
            "url": url,
            "status": "FAILED",
            "file": "",
            "size_bytes": 0,
            "error": error
        })

        print(f"  FAILED - {error}")

# Write collection log
with LOG_FILE.open("w", encoding="utf-8-sig", newline="") as f:
    fieldnames = [
        "url_id",
        "url",
        "status",
        "file",
        "size_bytes",
        "error"
    ]

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(log_rows)

success = sum(1 for r in log_rows if r["status"] == "SUCCESS")
failed = sum(1 for r in log_rows if r["status"] == "FAILED")

print()
print("COLLECTION COMPLETE")
print("-------------------")
print(f"Collections attempted: {len(rows)}")
print(f"Successful: {success}")
print(f"Failed: {failed}")
print(f"HTML folder: {OUTPUT_DIR}")
print(f"Log: {LOG_FILE}")