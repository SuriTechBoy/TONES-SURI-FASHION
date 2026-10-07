import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "03_STRUCTURED" / "product_search_index.json"
OUTPUT_FILE = BASE_DIR / "03_STRUCTURED" / "product_image_index.json"

with INPUT_FILE.open(encoding="utf-8") as f:
    data = json.load(f)

products = data if isinstance(data, list) else (
    data.get("products") or data.get("items") or []
)

print(f"Products found: {len(products)}")

results = {}
success = 0
failed = 0

def clean_url(value):
    if not value:
        return None

    value = value.strip()

    if value.startswith("//"):
        value = "https:" + value

    if value.startswith("http://"):
        value = "https://" + value[len("http://"):]

    return value

def extract_og_image(html):
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image:secure_url["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return clean_url(match.group(1))

    return None

def extract_jsonld_image(html):
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.IGNORECASE | re.DOTALL
    )

    for block in blocks:
        block = block.strip()

        try:
            obj = json.loads(block)
        except Exception:
            continue

        objects = obj if isinstance(obj, list) else [obj]

        for item in objects:
            if not isinstance(item, dict):
                continue

            image = item.get("image")

            if isinstance(image, str):
                image = clean_url(image)
                if image:
                    return image

            if isinstance(image, list) and image:
                for img in image:
                    if isinstance(img, str):
                        img = clean_url(img)
                        if img:
                            return img

            if isinstance(image, dict):
                image_url = image.get("url") or image.get("contentUrl")
                image_url = clean_url(image_url)
                if image_url:
                    return image_url

    return None

for i, product in enumerate(products, start=1):
    product_id = product.get("product_id")
    handle = product.get("handle")
    name = product.get("name")
    url = product.get("url")

    print(f"[{i}/{len(products)}] {name}")

    if not url:
        print("   FAILED: no product URL")
        failed += 1
        continue

    try:
        req = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/142 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml"
            }
        )

        with urlopen(req, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
            final_url = response.geturl()

        image_url = extract_og_image(html)

        if not image_url:
            image_url = extract_jsonld_image(html)

        if image_url:
            image_url = urljoin(final_url, image_url)

            results[product_id] = {
                "product_id": product_id,
                "handle": handle,
                "name": name,
                "product_url": url,
                "image_url": image_url,
                "source": "TONES product page",
                "source_type": "og:image/json-ld"
            }

            success += 1
            print(f"   OK: {image_url}")

        else:
            failed += 1
            print("   FAILED: image not found")

    except Exception as e:
        failed += 1
        print(f"   FAILED: {type(e).__name__}: {e}")

    time.sleep(0.25)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print()
print("=" * 60)
print("IMAGE COLLECTION COMPLETE")
print("=" * 60)
print(f"Products: {len(products)}")
print(f"Images found: {success}")
print(f"Images failed: {failed}")
print(f"Output: {OUTPUT_FILE}")
