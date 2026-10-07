import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "05_CANONICAL"
    / "products_canonical_with_collections.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "03_STRUCTURED"
    / "product_search_index.json"
)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


SIZE_PATTERN = re.compile(
    r"\b(XXL|XL|L|M|S)\b",
    re.IGNORECASE
)


def extract_field(description, field_name):
    """
    Extract a simple 'Field: value' from product description.
    Returns empty string when the source does not contain the field.
    """

    pattern = re.compile(
        rf"(?:^|\n)\s*{re.escape(field_name)}\s*:\s*([^\n]+)",
        re.IGNORECASE
    )

    match = pattern.search(
        description or ""
    )

    if match:
        return match.group(1).strip()

    return ""


def extract_sizes(variants):

    sizes = []

    for variant in variants:

        name = variant.get(
            "name",
            ""
        )

        match = SIZE_PATTERN.search(name)

        if match:

            size = match.group(1).upper()

            if size not in sizes:
                sizes.append(size)

    return sizes


def normalize_availability(value):

    value = str(value or "")

    if "InStock" in value:
        return "IN_STOCK"

    if "OutOfStock" in value:
        return "OUT_OF_STOCK"

    return "UNKNOWN"


with INPUT_FILE.open(
    encoding="utf-8"
) as f:

    products = json.load(f)


search_index = []


for product in products:

    description = product.get(
        "description",
        ""
    )

    variants = product.get(
        "variants",
        []
    )

    colors = extract_field(
        description,
        "Color"
    )

    fit = extract_field(
        description,
        "Fit"
    )

    fabric = extract_field(
        description,
        "Fabric"
    )

    sizes = extract_sizes(
        variants
    )

    in_stock_sizes = []

    variant_records = []

    for variant in variants:

        size_match = SIZE_PATTERN.search(
            variant.get("name", "")
        )

        size = (
            size_match.group(1).upper()
            if size_match
            else ""
        )

        availability = normalize_availability(
            variant.get("availability")
        )

        if (
            size
            and availability == "IN_STOCK"
            and size not in in_stock_sizes
        ):
            in_stock_sizes.append(size)

        variant_records.append({

            "variant_id": variant.get(
                "variant_id",
                ""
            ),

            "name": variant.get(
                "name",
                ""
            ),

            "sku": variant.get(
                "sku",
                ""
            ),

            "size": size,

            "price": variant.get(
                "price"
            ),

            "currency": variant.get(
                "currency",
                ""
            ),

            "availability": availability
        })


    prices = [
        v.get("price")
        for v in variants
        if isinstance(
            v.get("price"),
            (int, float)
        )
    ]


    collections = [
        item.get(
            "collection_url",
            ""
        )
        for item in product.get(
            "collections",
            []
        )
    ]


    search_index.append({

        "product_id": product.get(
            "product_id",
            ""
        ),

        "handle": product.get(
            "handle",
            ""
        ),

        "name": product.get(
            "name",
            ""
        ),

        "url": product.get(
            "url",
            ""
        ),

        "brand": product.get(
            "brand",
            ""
        ),

        "category": product.get(
            "category",
            ""
        ),

        "collections": collections,

        "color": colors,

        "fit": fit,

        "fabric": fabric,

        "price": product.get(
            "product_level_price"
        ),

        "currency": product.get(
            "currency",
            "INR"
        ),

        "min_variant_price": (
            min(prices)
            if prices
            else None
        ),

        "max_variant_price": (
            max(prices)
            if prices
            else None
        ),

        "sizes": sizes,

        "in_stock_sizes": in_stock_sizes,

        "variant_skus": [
            v.get("sku", "")
            for v in variants
            if v.get("sku")
        ],

        "variants": variant_records,

        "special_conditions": product.get(
            "special_conditions",
            []
        ),

        "validation_status": product.get(
            "validation",
            {}
        ).get(
            "status",
            ""
        )
    })


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        search_index,
        f,
        indent=2,
        ensure_ascii=False
    )


print()
print("TONES PRODUCT SEARCH INDEX")
print("=" * 60)

print(
    "Products:",
    len(search_index)
)

print(
    "Products with color:",
    sum(
        bool(p["color"])
        for p in search_index
    )
)

print(
    "Products with fit:",
    sum(
        bool(p["fit"])
        for p in search_index
    )
)

print(
    "Products with sizes:",
    sum(
        bool(p["sizes"])
        for p in search_index
    )
)

print(
    "Products with in-stock sizes:",
    sum(
        bool(p["in_stock_sizes"])
        for p in search_index
    )
)

print()
print(
    "Output:",
    OUTPUT_FILE
)