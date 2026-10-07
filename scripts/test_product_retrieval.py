import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "06_RAG"
    / "product_chunks.jsonl"
)


with INPUT_FILE.open(
    encoding="utf-8"
) as f:
    chunks = [
        json.loads(line)
        for line in f
        if line.strip()
    ]


def extract_price(chunk):
    metadata = chunk.get("metadata", {})

    price = metadata.get("price")

    if price is not None:
        try:
            return float(price)
        except (ValueError, TypeError):
            pass

    text = chunk.get("text", "")

    matches = re.findall(
        r"(?:₹|Rs\.?|INR)\s*([\d,]+)",
        text,
        re.IGNORECASE
    )

    if matches:
        try:
            return float(
                matches[0].replace(",", "")
            )
        except ValueError:
            pass

    return None


def search_products(query, top_k=5):

    query_lower = query.lower()

    query_words = set(
        re.findall(
            r"\b[a-z0-9]+\b",
            query_lower
        )
    )

    results = []

    for chunk in chunks:

        name = chunk.get(
            "name",
            ""
        ).lower()

        text = chunk.get(
            "text",
            ""
        ).lower()

        metadata = chunk.get(
            "metadata",
            {}
        )

        category = metadata.get(
            "category",
            ""
        ).lower()

        searchable = (
            name
            + " "
            + text
            + " "
            + category
        )

        score = 0

        # Exact product-name match
        if query_lower in name:
            score += 10

        # Name word matches
        for word in query_words:

            if word in name:
                score += 4

            elif word in category:
                score += 3

            elif word in text:
                score += 1

        # Size matching
        variants = chunk.get(
            "text",
            ""
        ).lower()

        if "xl" in query_words and "xl" in variants:
            score += 3

        # Product result
        if score > 0:

            results.append(
                (
                    score,
                    chunk
                )
            )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:top_k]


queries = [
    "black oversized t shirt",
    "Daily Tees",
    "XL size",
    "sweatshirt",
]


print()
print("TONES PRODUCT RETRIEVAL TEST")
print("=" * 60)


for query in queries:

    print()
    print("QUERY:", query)
    print("-" * 60)

    results = search_products(query)

    if not results:
        print("No results")
        continue

    for rank, (score, chunk) in enumerate(
        results,
        start=1
    ):

        print(
            f"{rank}. "
            f"{chunk.get('name')} "
            f"| Score: {score}"
        )