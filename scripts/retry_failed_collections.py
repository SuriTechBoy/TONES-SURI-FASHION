import csv
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_FILE = BASE_DIR / "01_RAW_DATA" / "collection_collection_log.csv"
OUTPUT_DIR = BASE_DIR / "01_RAW_DATA" / "collections_html"

SHOPIFY_IP = "23.227.38.32"
DOMAIN = "www.tonesfashion.com"

RETRY_WAIT_SECONDS = 12

# Read current collection log
with LOG_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

failed_rows = [
    row for row in rows
    if row["status"] == "FAILED"
]

print(f"Failed collections to retry: {len(failed_rows)}")
print()

for index, row in enumerate(failed_rows, start=1):

    url_id = row["url_id"]
    url = row["url"]

    output_file = OUTPUT_DIR / f"{url_id}.html"

    print(f"[{index}/{len(failed_rows)}] Retrying {url_id}")
    print(f"  URL: {url}")

    command = [
        "curl.exe",
        "-L",
        "--silent",
        "--show-error",
        "--fail",
        "--retry",
        "2",
        "--retry-delay",
        "10",
        "--resolve",
        f"{DOMAIN}:443:{SHOPIFY_IP}",
        "-A",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142.0 Safari/537.36",
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

        row["status"] = "SUCCESS"
        row["file"] = str(output_file.relative_to(BASE_DIR))
        row["size_bytes"] = size
        row["error"] = ""

        print(f"  SUCCESS - {size:,} bytes")

    else:
        error = result.stderr.strip()

        if output_file.exists():
            output_file.unlink()

        row["status"] = "FAILED"
        row["file"] = ""
        row["size_bytes"] = "0"
        row["error"] = error

        print(f"  FAILED - {error}")

    # Delay before next request
    if index < len(failed_rows):
        print(f"  Waiting {RETRY_WAIT_SECONDS} seconds...")
        time.sleep(RETRY_WAIT_SECONDS)

# Rewrite the complete log
fieldnames = [
    "url_id",
    "url",
    "status",
    "file",
    "size_bytes",
    "error"
]

with LOG_FILE.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

success = sum(1 for row in rows if row["status"] == "SUCCESS")
failed = sum(1 for row in rows if row["status"] == "FAILED")

print()
print("RETRY COMPLETE")
print("--------------")
print(f"Total collections: {len(rows)}")
print(f"Successful: {success}")
print(f"Failed: {failed}")
print(f"Log updated: {LOG_FILE}")