import json
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


checks = {
    "missing_chunk_id": 0,
    "missing_product_id": 0,
    "missing_handle": 0,
    "missing_name": 0,
    "missing_text": 0,
    "missing_url": 0,
    "missing_variant_skus": 0,
    "missing_metadata": 0,
}


for chunk in chunks:

    if not chunk.get("chunk_id"):
        checks["missing_chunk_id"] += 1

    if not chunk.get("product_id"):
        checks["missing_product_id"] += 1

    if not chunk.get("handle"):
        checks["missing_handle"] += 1

    if not chunk.get("name"):
        checks["missing_name"] += 1

    if not chunk.get("text"):
        checks["missing_text"] += 1

    if not chunk.get("metadata", {}).get("url"):
        checks["missing_url"] += 1

        if not chunk.get("metadata", {}).get("variant_skus"):
            checks["missing_variant_skus"] += 1

    if not chunk.get("metadata"):
        checks["missing_metadata"] += 1


print()
print("RAG CHUNK QUALITY CHECK")
print("=" * 60)

print("Total chunks:", len(chunks))
print()

for check, count in checks.items():

    print(
        check + ":",
        count
    )

print()

if all(count == 0 for count in checks.values()):

    print("RESULT: PASS")

else:

    print("RESULT: REVIEW REQUIRED")