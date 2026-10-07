import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

JSON_DIR = BASE_DIR / "01_RAW_DATA" / "products_json"
VALIDATION_FILE = BASE_DIR / "04_VALIDATED" / "product_data_validation.csv"
ANOMALY_FILE = BASE_DIR / "04_VALIDATED" / "product_anomalies.csv"

OUTPUT_FILE = BASE_DIR / "05_CANONICAL" / "products_canonical.json"


OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load validation information
# ---------------------------------------------------------

validation = {}

with VALIDATION_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as f:

    for row in csv.DictReader(f):
        validation[row["file"]] = row


# ---------------------------------------------------------
# Load anomaly information
# ---------------------------------------------------------

anomalies = {}

with ANOMALY_FILE.open(
    encoding="utf-8-sig",
    newline=""
) as f:

    for row in csv.DictReader(f):
        anomalies[row["product_name"]] = row


# ---------------------------------------------------------
# Convert products
# ---------------------------------------------------------

canonical_products = []


for json_file in sorted(JSON_DIR.glob("*.json")):

    with json_file.open(encoding="utf-8") as f:
        product = json.load(f)

    name = product.get("name", "")
    sku = product.get("sku", "")

    variants = product.get("variants", [])

    if not isinstance(variants, list):
        variants = []


    # -----------------------------------------------------
    # Product images
    # -----------------------------------------------------

    image_urls = set()

    product_images = product.get("image", [])

    if isinstance(product_images, list):

        for image in product_images:

            if isinstance(image, str) and image.strip():
                image_urls.add(image.strip())

    elif isinstance(product_images, str):

        if product_images.strip():
            image_urls.add(product_images.strip())


    # -----------------------------------------------------
    # Variants
    # -----------------------------------------------------

    canonical_variants = []

    prices = []

    for index, variant in enumerate(variants):

        if not isinstance(variant, dict):
            continue

        price = variant.get("price")

        if price not in (None, ""):

            try:
                price_number = float(price)
                prices.append(price_number)
            except (ValueError, TypeError):
                price_number = None

        else:
            price_number = None


        compare_price = variant.get("compare_at_price")

        if compare_price not in (None, ""):

            try:
                compare_price_number = float(compare_price)
            except (ValueError, TypeError):
                compare_price_number = None

        else:
            compare_price_number = None


        variant_image = variant.get("image", "")

        if isinstance(variant_image, str):

            if variant_image.strip():
                image_urls.add(variant_image.strip())

        elif isinstance(variant_image, list):

            for image in variant_image:

                if isinstance(image, str) and image.strip():
                    image_urls.add(image.strip())


        availability = variant.get(
            "availability",
            ""
        )


        canonical_variants.append({
            "variant_id": f"{sku or json_file.stem}-V{index + 1}",
            "name": variant.get("name", ""),
            "sku": variant.get("sku", ""),
            "size": "",
            "color": "",
            "price": price_number,
            "compare_at_price": compare_price_number,
            "currency": variant.get("currency", "INR"),
            "availability": availability,
            "image": variant_image
        })


    # -----------------------------------------------------
    # Product-level price
    # -----------------------------------------------------

    product_level_price = None

    if prices:
        product_level_price = min(prices)


    # -----------------------------------------------------
    # Special conditions
    # -----------------------------------------------------

    special_conditions = []

    description = product.get("description", "")

    if isinstance(description, str):

        lower_description = description.lower()

        if "no returns and exchanges" in lower_description:

            special_conditions.append(
                "No Returns and Exchanges on this Product"
            )


    # -----------------------------------------------------
    # Validation status
    # -----------------------------------------------------

    validation_row = validation.get(
        json_file.name,
        {}
    )

    issues = []

    if not validation_row.get("name"):
        issues.append("Missing product name")

    if int(validation_row.get("variant_count", 0)) == 0:

        issues.append(
            "No variants captured"
        )

    if int(validation_row.get("price_count", 0)) == 0:

        issues.append(
            "No price captured"
        )


    if issues:

        validation_status = "NEEDS_VERIFICATION"

    else:

        validation_status = "VALIDATED"


    if name in anomalies:

        anomaly = anomalies[name]

        classification = anomaly.get(
            "classification",
            ""
        )

        if classification == "ALL_VARIANTS_OUT_OF_STOCK":

            issues.append(
                "All captured variants are OutOfStock"
            )


    # -----------------------------------------------------
    # Build canonical record
    # -----------------------------------------------------

    canonical_product = {

        "product_id": sku or json_file.stem,

        "handle": "",

        "name": name,

        "sku": sku,

        "url": product.get(
            "url",
            product.get("source_url", "")
        ),

        "brand": product.get(
            "brand",
            ""
        ),

        "category": product.get(
            "category",
            ""
        ),

        "collections": [],

        "description": description,

        "images": sorted(image_urls),

        "variants": canonical_variants,

        "product_level_price": product_level_price,

        "currency": "INR",

        "special_conditions": special_conditions,

        "customer_facing_notes": [],

        "source": {

            "source_url": product.get(
                "source_url",
                ""
            ),

            "collection_method": product.get(
                "collection_method",
                ""
            ),

            "collected_at": product.get(
                "collected_at",
                ""
            )
        },

        "validation": {

            "status": validation_status,

            "issues": issues,

            "last_validated": ""
        }
    }


    canonical_products.append(
        canonical_product
    )


# ---------------------------------------------------------
# Save canonical products
# ---------------------------------------------------------

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        canonical_products,
        f,
        indent=2,
        ensure_ascii=False
    )


print()
print("CANONICAL PRODUCT BUILD")
print("=" * 60)

print(
    "Products converted:",
    len(canonical_products)
)

print(
    "Validated:",
    sum(
        p["validation"]["status"] == "VALIDATED"
        for p in canonical_products
    )
)

print(
    "Needs verification:",
    sum(
        p["validation"]["status"] == "NEEDS_VERIFICATION"
        for p in canonical_products
    )
)

print()
print("Output:", OUTPUT_FILE)