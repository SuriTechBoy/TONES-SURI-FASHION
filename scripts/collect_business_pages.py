from __future__ import annotations

import csv
import hashlib
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "01_RAW_DATA" / "business_pages"
RAW.mkdir(parents=True, exist_ok=True)

LOG = ROOT / "01_RAW_DATA" / "business_pages_collection_log.csv"


# ============================================================
# TONES CONNECTION
# ============================================================

TONES_IP = "23.227.38.32"

TONES_HOST = "www.tonesfashion.com"


# ============================================================
# BUSINESS PAGE SOURCES
# ============================================================

PAGES = [
    (
        "TONES-BIZ-0001",
        "HOME",
        "Brand",
        "TONES Fashion",
        "https://www.tonesfashion.com/",
    ),
    (
        "TONES-BIZ-0002",
        "ABOUT",
        "Business",
        "About Us",
        "https://www.tonesfashion.com/pages/about",
    ),
    (
        "TONES-BIZ-0003",
        "CONTACT",
        "Business",
        "Contact Us",
        "https://www.tonesfashion.com/pages/contact",
    ),
    (
        "TONES-BIZ-0004",
        "SHIPPING",
        "Policy",
        "Shipping and Delivery Policy",
        "https://www.tonesfashion.com/policies/shipping-policy",
    ),
    (
        "TONES-BIZ-0005",
        "RETURNS",
        "Policy",
        "Return & Exchange Policy",
        "https://www.tonesfashion.com/pages/return-exchange-policy",
    ),
    (
        "TONES-BIZ-0006",
        "TERMS",
        "Policy",
        "Terms of Service",
        "https://www.tonesfashion.com/policies/terms-of-service",
    ),
    (
        "TONES-BIZ-0007",
        "PRIVACY",
        "Policy",
        "Privacy Policy",
        "https://www.tonesfashion.com/policies/privacy-policy",
    ),
    (
        "TONES-BIZ-0008",
        "ORDER_TRACKING",
        "Order",
        "Track Order",
        "https://1093.logisy.tech/track-order/",
    ),
    (
        "TONES-BIZ-0009",
        "RETURN_REQUEST",
        "Order",
        "Exchange/Return Request",
        "https://returns.logisy.tech/returns",
    ),
    (
        "TONES-BIZ-0010",
        "BLOG_INDEX",
        "Content",
        "Blogs",
        "https://www.tonesfashion.com/blogs/news",
    ),
    (
        "TONES-BIZ-0011",
        "FAQ",
        "Customer Knowledge",
        "FAQ",
        "https://www.tonesfashion.com/pages/faq",
    ),
]


# ============================================================
# USER AGENT
# ============================================================

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0.0.0 Safari/537.36"
)


# ============================================================
# CURL COLLECTION
# ============================================================

def collect_with_curl(url: str, output_file: Path) -> tuple[int, str, str]:
    """
    Download a page using curl.

    For TONES www hostname, use:

        --resolve www.tonesfashion.com:443:23.227.38.32

    This is the same method that was manually verified with HTTP 200.
    """

    command = [
        "curl.exe",

        "--silent",
        "--show-error",
        "--location",

        "--connect-timeout",
        "20",

        "--max-time",
        "60",

        "--retry",
        "2",

        "--retry-delay",
        "1",

        "--user-agent",
        USER_AGENT,

        "--resolve",
        f"{TONES_HOST}:443:{TONES_IP}",

        "--output",
        str(output_file),

        url,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    error_text = result.stderr.strip()

    if result.returncode != 0:
        raise RuntimeError(
            f"curl failed with exit code "
            f"{result.returncode}: {error_text}"
        )

    # Get the final HTTP status separately.
    status_command = [
        "curl.exe",

        "--silent",
        "--show-error",
        "--location",

        "--connect-timeout",
        "20",

        "--max-time",
        "60",

        "--retry",
        "2",
        "--retry-delay",
        "1",

        "--user-agent",
        USER_AGENT,

        "--resolve",
        f"{TONES_HOST}:443:{TONES_IP}",

        "--write-out",
        "%{http_code}|%{url_effective}",

        "--output",
        "NUL",

        url,
    ]

    status_result = subprocess.run(
        status_command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    if status_result.returncode != 0:
        raise RuntimeError(
            status_result.stderr.strip()
        )

    status_output = status_result.stdout.strip()

    if "|" in status_output:
        status_text, final_url = status_output.split(
            "|",
            1,
        )
    else:
        status_text = status_output
        final_url = url

    try:
        status_code = int(status_text)
    except ValueError:
        status_code = 0

    return (
        status_code,
        final_url,
        error_text,
    )


# ============================================================
# COLLECTION
# ============================================================

rows = []

for source_id, page_type, category, title, url in PAGES:

    collected_at = datetime.now(
        timezone.utc
    ).isoformat()

    row = {
        "source_id": source_id,
        "page_type": page_type,
        "category": category,
        "title": title,
        "url": url,
        "collected_at": collected_at,
        "status": "FAILED",
        "http_status": "",
        "file": "",
        "sha256": "",
        "error": "",
        "final_url": "",
    }

    print()
    print("=" * 70)
    print(f"Collecting: {title}")
    print(f"URL:        {url}")

    try:

        output_file = RAW / f"{source_id.lower()}.html"

        # Use curl --resolve for TONES pages.
        # For external Logisy pages, the same command works normally.
        status_code, final_url, curl_error = collect_with_curl(
            url,
            output_file,
        )

        row["http_status"] = status_code
        row["final_url"] = final_url

        if status_code >= 200 and status_code < 400:

            content = output_file.read_bytes()

            row["status"] = "SUCCESS"

            row["file"] = str(
                output_file.relative_to(ROOT)
            ).replace("\\", "/")

            row["sha256"] = hashlib.sha256(
                content
            ).hexdigest()

            print(
                f"SUCCESS | HTTP {status_code}"
            )

            print(
                f"Saved: {output_file}"
            )

        else:

            row["status"] = "HTTP_ERROR"

            row["file"] = str(
                output_file.relative_to(ROOT)
            ).replace("\\", "/")

            if curl_error:
                row["error"] = curl_error

            print(
                f"HTTP ERROR | HTTP {status_code}"
            )

    except Exception as exc:

        row["status"] = "FAILED"
        row["error"] = repr(exc)

        print(
            f"FAILED | {exc}"
        )

    rows.append(row)

    time.sleep(0.5)


# ============================================================
# WRITE COLLECTION LOG
# ============================================================

with LOG.open(
    "w",
    newline="",
    encoding="utf-8",
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "source_id",
            "page_type",
            "category",
            "title",
            "url",
            "collected_at",
            "status",
            "http_status",
            "file",
            "sha256",
            "error",
            "final_url",
        ],
    )

    writer.writeheader()
    writer.writerows(rows)


# ============================================================
# SUMMARY
# ============================================================

success_count = sum(
    row["status"] == "SUCCESS"
    for row in rows
)

failed_count = sum(
    row["status"] == "FAILED"
    for row in rows
)

http_error_count = sum(
    row["status"] == "HTTP_ERROR"
    for row in rows
)


print()
print("=" * 70)
print("TONES BUSINESS PAGE COLLECTION SUMMARY")
print("=" * 70)

print(
    f"Total pages:       {len(rows)}"
)

print(
    f"Successful:        {success_count}"
)

print(
    f"Failed:            {failed_count}"
)

print(
    f"HTTP errors:       {http_error_count}"
)

print(
    f"Collection log:    {LOG}"
)

print("=" * 70)