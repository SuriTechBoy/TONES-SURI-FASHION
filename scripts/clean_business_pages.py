"""Convert collected business-page HTML into clean text/Markdown files."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "01_RAW_DATA" / "business_pages"
OUT = ROOT / "02_CLEANED" / "business_pages"
LOG = ROOT / "01_RAW_DATA" / "business_pages_collection_log.csv"
OUT.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(LOG.open(encoding="utf-8"))) if LOG.exists() else []

for row in rows:
    if row.get("status") != "SUCCESS" or not row.get("file"):
        continue
    src = ROOT / row["file"]
    if not src.exists():
        continue
    soup = BeautifulSoup(src.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    main = soup.find("main") or soup.find("body") or soup
    text = main.get_text("\n", strip=True)
    lines = []
    previous = None
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line == previous:
            continue
        lines.append(line)
        previous = line
    content = "\n".join(lines) + "\n"
    out = OUT / f"{row['source_id'].lower()}.txt"
    out.write_text(content, encoding="utf-8")

print(f"Cleaned files written to: {OUT}")
