import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "05_CANONICAL"
    / "products_canonical_with_collections.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "06_RAG"
    / "product_chunks.jsonl"
)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


with INPUT_FILE.open(
    encoding="utf-8"
) as f:
    products = json.load(f)


chunks = []


for product in products:

    collection_text = "\n".join(
        [
            item["collection_id"]
            + " | "
            + item["collection_url"]
            for item in product.get("collections", [])
        ]
    )

    variant_text = []

    for variant in product.get("variants", []):

        variant_text.append(
            "Variant: "
            + str(variant.get("name", ""))
            + "\n"
            + "SKU: "
            + str(variant.get("sku", ""))
            + "\n"
            + "Price: "
            + str(variant.get("price", ""))
            + " "
            + str(variant.get("currency", ""))
            + "\n"
            + "Availability: "
            + str(variant.get("availability", ""))
        )

    variant_text = "\n\n".join(
        variant_text
    )

    special_conditions = "\n".join(
        product.get(
            "special_conditions",
            []
        )
    )

    # Customer-facing RAG text
    # IMPORTANT: Do not put Python source code inside this text.
    text = f"""
Product Name: {product.get('name', '')}

Brand: {product.get('brand', '')}

Product URL: {product.get('url', '')}

Category: {product.get('category', '')}

Description:
{product.get('description', '')}

Collections:
{collection_text}

Variants:
{variant_text}

Special Conditions:
{special_conditions}

Product Price:
{product.get('product_level_price', '')}

Currency:
{product.get('currency', '')}
""".strip()


    chunks.append({

        "chunk_id": (
            "product_"
            + product.get("handle", "")
        ),

        "document_type": "product",

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

        "text": text,

        "metadata": {

            "brand": product.get(
                "brand",
                ""
            ),

            "category": product.get(
                "category",
                ""
            ),

            "sku": product.get(
                "sku",
                ""
            ),

            "variant_skus": [
                v.get("sku", "")
                for v in product.get("variants", [])
                if v.get("sku")
            ],

            "url": product.get(
                "url",
                ""
            ),

            "validation_status": product.get(
                "validation",
                {}
            ).get(
                "status",
                ""
            )
        }
    })


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as f:

    for chunk in chunks:

        f.write(
            json.dumps(
                chunk,
                ensure_ascii=False
            )
            + "\n"
        )


print()
print("RAG PRODUCT CHUNKS")
print("=" * 60)

print(
    "Products:",
    len(products)
)

print(
    "Chunks:",
    len(chunks)
)

print()
print("Output:", OUTPUT_FILE)