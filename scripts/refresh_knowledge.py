"""Refresh TONES product pages from Shopify sitemaps, then rebuild the local KB.

Run this on a machine with internet access. It intentionally keeps the old
snapshot until the new scrape has completed, so a failed refresh never destroys
working knowledge.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "01_RAW_DATA" / "products_html"
TMP = ROOT / ".refresh_tmp"
BASE = "https://www.tonesfashion.com"


def urls_from_sitemap(url: str) -> list[str]:
    r = requests.get(url, timeout=30, headers={"User-Agent": "TONES-Knowledge-Refresh/2.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    return [loc.get_text(strip=True) for loc in soup.find_all("loc")]


def collect_product_urls() -> list[str]:
    candidates = [f"{BASE}/sitemap_products_1.xml", f"{BASE}/sitemap_products_2.xml", f"{BASE}/sitemap_products_3.xml"]
    urls=[]
    for sitemap in candidates:
        try:
            urls.extend(urls_from_sitemap(sitemap))
        except requests.RequestException:
            continue
    return sorted(set(u for u in urls if "/products/" in u))


def main():
    TMP.mkdir(exist_ok=True)
    urls = collect_product_urls()
    if not urls:
        raise SystemExit("No product URLs were collected. Existing knowledge was left untouched.")
    staging = TMP / "products_html"
    if staging.exists(): shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for i, url in enumerate(urls, 1):
        r=requests.get(url,timeout=30,headers={"User-Agent":"TONES-Knowledge-Refresh/2.0"})
        r.raise_for_status()
        handle=urlparse(url).path.rstrip('/').split('/')[-1]
        (staging/f"LIVE-{i:04d}-{handle}.html").write_text(r.text,encoding='utf-8')
        print(f"[{i}/{len(urls)}] {handle}")

    # Keep a timestamped live snapshot separately; the deterministic v2 build
    # can then be adapted to the live IDs if needed.
    target=ROOT/'01_RAW_DATA'/'live_products_html'
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(staging,target)
    print(f"Saved {len(urls)} live product pages to {target}")
    print("Next: run scripts/extract_reviews.py and scripts/build_tones_knowledge.py after mapping live pages into the canonical IDs.")

if __name__=='__main__': main()
