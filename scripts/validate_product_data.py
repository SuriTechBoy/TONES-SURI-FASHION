import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

JSON_DIR = BASE_DIR / "01_RAW_DATA" / "products_json"
OUTPUT_FILE = BASE_DIR / "04_VALIDATED" / "product_data_validation.csv"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

results = []


for json_file in sorted(JSON_DIR.glob("*.json")):

    try:
        with json_file.open(encoding="utf-8") as f:
            product = json.load(f)

        name = product.get("name", "")
        handle = product.get("handle", "")
        description = product.get("description", "")
        vendor = product.get("vendor", "")
        product_type = product.get("type", "")

        variants = product.get("variants", [])

        if not isinstance(variants, list):
            variants = []

        prices = []
        compare_prices = []

        in_stock_variants = 0
        out_of_stock_variants = 0

        variant_image_count = 0

        for variant in variants:

            if not isinstance(variant, dict):
                continue

            # Price
            price = variant.get("price")

            if price not in (None, ""):
                prices.append(str(price))

            # Compare-at price
            compare_price = variant.get("compare_at_price")

            if compare_price not in (None, ""):
                compare_prices.append(str(compare_price))

            # Availability
            availability = str(
                variant.get("availability", "")
            ).lower()

            if "instock" in availability:
                in_stock_variants += 1

            elif "outofstock" in availability:
                out_of_stock_variants += 1

            # Variant image
            variant_image = variant.get("image")

            if isinstance(variant_image, str):
                if variant_image.strip():
                    variant_image_count += 1

            elif isinstance(variant_image, list):
                variant_image_count += len(
                    [
                        x for x in variant_image
                        if isinstance(x, str) and x.strip()
                    ]
                )

        # Product-level images
        product_image = product.get("image", [])

        product_image_count = 0

        if isinstance(product_image, list):

            product_image_count = len(
                [
                    x for x in product_image
                    if isinstance(x, str) and x.strip()
                ]
            )

        elif isinstance(product_image, str):

            if product_image.strip():
                product_image_count = 1

        # Total unique image URLs
        image_urls = set()

        if isinstance(product_image, list):

            for image in product_image:
                if isinstance(image, str) and image.strip():
                    image_urls.add(image)

        elif isinstance(product_image, str):

            if product_image.strip():
                image_urls.add(product_image)

        for variant in variants:

            if not isinstance(variant, dict):
                continue

            variant_image = variant.get("image")

            if isinstance(variant_image, str):

                if variant_image.strip():
                    image_urls.add(variant_image)

            elif isinstance(variant_image, list):

                for image in variant_image:

                    if isinstance(image, str) and image.strip():
                        image_urls.add(image)

        results.append({
            "file": json_file.name,
            "handle": handle,
            "name": name,
            "vendor": vendor,
            "product_type": product_type,
            "description_present": bool(
                isinstance(description, str)
                and description.strip()
            ),
            "variant_count": len(variants),
            "in_stock_variants": in_stock_variants,
            "out_of_stock_variants": out_of_stock_variants,
            "price_count": len(prices),
            "compare_price_count": len(compare_prices),
            "product_image_count": product_image_count,
            "variant_image_count": variant_image_count,
            "total_unique_images": len(image_urls),
        })

    except Exception as e:

        print(
            f"ERROR processing {json_file.name}: {e}"
        )

        results.append({
            "file": json_file.name,
            "handle": "",
            "name": "",
            "vendor": "",
            "product_type": "",
            "description_present": False,
            "variant_count": 0,
            "in_stock_variants": 0,
            "out_of_stock_variants": 0,
            "price_count": 0,
            "compare_price_count": 0,
            "product_image_count": 0,
            "variant_image_count": 0,
            "total_unique_images": 0,
        })


fieldnames = [
    "file",
    "handle",
    "name",
    "vendor",
    "product_type",
    "description_present",
    "variant_count",
    "in_stock_variants",
    "out_of_stock_variants",
    "price_count",
    "compare_price_count",
    "product_image_count",
    "variant_image_count",
    "total_unique_images",
]


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(results)


print()
print("PRODUCT DATA VALIDATION")
print("=" * 60)

print("JSON files checked:", len(results))

print(
    "With product name:",
    sum(bool(r["name"]) for r in results)
)

print(
    "With variants:",
    sum(r["variant_count"] > 0 for r in results)
)

print(
    "With description:",
    sum(r["description_present"] for r in results)
)

print(
    "With price:",
    sum(r["price_count"] > 0 for r in results)
)

print(
    "With images:",
    sum(r["total_unique_images"] > 0 for r in results)
)

print(
    "With in-stock variants:",
    sum(r["in_stock_variants"] > 0 for r in results)
)

print()
print("Output:", OUTPUT_FILE)