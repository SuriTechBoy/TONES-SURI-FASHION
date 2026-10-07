from pathlib import Path
import shutil
import re
import json
import py_compile

ROOT = Path(__file__).resolve().parents[1]

LLM = ROOT / "scripts" / "llm_adapter.py"
API = ROOT / "api" / "main.py"
STRUCTURED = ROOT / "scripts" / "structured_product_search.py"
INDEX = ROOT / "03_STRUCTURED" / "product_search_index.json"


def backup(path):
    backup_path = path.with_suffix(path.suffix + ".bak_final2")
    if not backup_path.exists():
        shutil.copy2(path, backup_path)
        print(f"BACKUP: {backup_path}")
    else:
        print(f"BACKUP EXISTS: {backup_path}")


def read(path):
    return path.read_text(encoding="utf-8")


def write(path, text):
    path.write_text(text, encoding="utf-8")
    print(f"UPDATED: {path}")


# ============================================================
# 1. LLM ADAPTER - FORCE ATTRIBUTE CLARIFICATION
# ============================================================

backup(LLM)
text = read(LLM)

marker = "operation = special_intent or special_operation"

if marker in text:
    clarification = '''
# ---------------------------------------------------------
# Deterministic product-attribute clarification
# ---------------------------------------------------------
if (
    special_operation == "PRODUCT_ATTRIBUTE_CLARIFICATION"
    or (
        special_intent in {
            "PRODUCT_FABRIC",
            "PRODUCT_SIZE",
            "PRODUCT_FIT",
            "PRODUCT_MATERIAL",
        }
        and special_operation == "PRODUCT_ATTRIBUTE_CLARIFICATION"
    )
):
    attribute_prompts = {
        "PRODUCT_FABRIC":
            "Sure. Which TONES Fashion product would you like to know "
            "the fabric details for? Please provide the product name.",

        "PRODUCT_SIZE":
            "Sure. Which TONES Fashion product would you like to know "
            "the available sizes for? Please provide the product name.",

        "PRODUCT_FIT":
            "Sure. Which TONES Fashion product would you like to know "
            "the fit details for? Please provide the product name.",

        "PRODUCT_MATERIAL":
            "Sure. Which TONES Fashion product would you like to know "
            "the material details for? Please provide the product name.",
    }

    if special_intent in attribute_prompts:
        return attribute_prompts[special_intent]

    if attribute_type in attribute_prompts:
        return attribute_prompts[attribute_type]

operation = special_intent or special_operation
'''

    text = text.replace(marker, clarification, 1)
    print("LLM: deterministic attribute clarification inserted")
else:
    print("ERROR: operation marker not found")


# ============================================================
# 2. LLM - NORMALIZE GENERATED BULLETS / DASHES
# ============================================================

text = text.replace("• ", "- ")
text = text.replace(" — ", " - ")
text = text.replace("–", "- ")
text = text.replace("—", " - ")

write(LLM, text)


# ============================================================
# 3. API - PREVENT SALE CARD LEAKAGE
# ============================================================

backup(API)
api = read(API)

# Insert a deterministic aggregation guard immediately before
# normal product-card construction.
anchor = 'products = []'

if anchor in api:

    guard = '''
# ---------------------------------------------------------
# Deterministic special-operation product-card safety
# ---------------------------------------------------------
special_operation = context.get("special_operation")
special_intent = context.get("special_intent")

# A sale query must NEVER display ordinary products when
# verified sale products were not found.
if (
    special_operation == "PRODUCTS_ON_SALE"
    or special_intent == "PRODUCTS_ON_SALE"
):
    sale_products = []

    for item in context.get("products", []) or []:
        try:
            price = item.get("price")
            compare_at = item.get("compare_at_price")

            if (
                price is not None
                and compare_at is not None
                and float(compare_at) > float(price)
            ):
                sale_products.append(item)
        except (TypeError, ValueError):
            continue

    context["products"] = sale_products

'''

    # Only insert if not already present.
    if "Deterministic special-operation product-card safety" not in api:
        api = api.replace(anchor, guard + anchor, 1)
        print("API: sale-card leakage guard inserted")
    else:
        print("API: sale-card leakage guard already exists")
else:
    print("ERROR: API product-card anchor not found")


write(API, api)


# ============================================================
# 4. STRUCTURED PRODUCT SEARCH - DISPLAY NORMALIZATION
# ============================================================

backup(STRUCTURED)
structured = read(STRUCTURED)

# Add a small helper after imports.
helper_marker = "def "

helper = '''

# ============================================================
# Text normalization for UTF-8 mojibake from scraped data
# ============================================================

def normalize_scraped_text(value):
    """
    Repair common UTF-8/Windows mojibake without inventing
    product facts.

    Example:
        'â Grey' -> '- Grey'
        'Â Fabric' -> 'Fabric'
    """
    if not isinstance(value, str):
        return value

    replacements = {
        "â€“": "-",
        "â€”": "-",
        "â€" : "",
        "â¢": "-",
        "Â ": " ",
        "Â": "",
    }

    result = value

    for bad, good in replacements.items():
        result = result.replace(bad, good)

    # Common malformed separator patterns.
    result = result.replace(" â ", " - ")
    result = result.replace("â ", "- ")
    result = result.replace("Â ", " ")

    return result.strip()


def normalize_product_record(record):
    if not isinstance(record, dict):
        return record

    for key, value in list(record.items()):
        if isinstance(value, str):
            record[key] = normalize_scraped_text(value)

        elif isinstance(value, list):
            record[key] = [
                normalize_scraped_text(x) if isinstance(x, str) else x
                for x in value
            ]

    return record

'''

# Find the first function definition and insert helper before it.
if "def normalize_scraped_text(value):" not in structured:
    idx = structured.find("def ")
    if idx != -1:
        structured = structured[:idx] + helper + "\n" + structured[idx:]
        print("STRUCTURED: normalization helper inserted")
    else:
        print("STRUCTURED: no function definition found")
else:
    print("STRUCTURED: normalization helper already exists")


# Try to normalize product records after JSON loading.
# We target common assignment patterns without destroying the file.
patterns = [
    (
        r'(\bproducts\s*=\s*json\.load\([^)]+\))',
        r'\1\nproducts = [normalize_product_record(p) for p in products]'
    ),
    (
        r'(\bdata\s*=\s*json\.load\([^)]+\))',
        r'\1\nif isinstance(data, list):\n    data = [normalize_product_record(p) for p in data]'
    ),
]

for pattern, replacement in patterns:
    if re.search(pattern, structured):
        structured = re.sub(pattern, replacement, structured, count=1)
        print("STRUCTURED: product normalization hook inserted")
        break
else:
    print("STRUCTURED: automatic normalization hook not inserted")
    print("          Existing loader will be inspected separately.")

write(STRUCTURED, structured)


# ============================================================
# 5. VALIDATE JSON WITHOUT MODIFYING PRODUCT FACTS
# ============================================================

print()
print("=" * 70)
print("PRODUCT DATA VALIDATION REPORT")
print("=" * 70)

if INDEX.exists():
    data = json.loads(INDEX.read_text(encoding="utf-8"))

    products = data if isinstance(data, list) else data.get("products", [])

    conflicts = 0

    for i, p in enumerate(products):
        name = str(p.get("name", ""))
        url = str(p.get("url", ""))
        color = str(p.get("color", ""))

        # Name vs color
        name_lower = name.lower()
        color_lower = color.lower()

        if color and color_lower not in {"none", "null"}:
            color_words = {
                "black": "black",
                "white": "white",
                "grey": "grey",
                "gray": "gray",
                "green": "green",
                "blue": "blue",
                "red": "red",
                "orange": "orange",
                "brown": "brown",
                "beige": "beige",
                "pink": "pink",
                "yellow": "yellow",
                "maroon": "maroon",
            }

            for word, expected in color_words.items():
                if word in name_lower and expected != color_lower:
                    print(
                        f"[POSSIBLE COLOR CONFLICT] "
                        f"{name} | structured color={color}"
                    )
                    conflicts += 1
                    break

        # Name vs URL color hints
        color_hints = [
            "black", "white", "grey", "gray", "blue",
            "green", "red", "orange", "brown", "beige",
            "pink", "yellow", "maroon"
        ]

        name_colors = [c for c in color_hints if c in name_lower]
        url_colors = [c for c in color_hints if c in url.lower()]

        if name_colors and url_colors:
            if not any(c in url_colors for c in name_colors):
                print(
                    f"[POSSIBLE NAME/URL CONFLICT] "
                    f"{name} | URL={url}"
                )
                conflicts += 1

        # Missing important fields
        if not p.get("name"):
            print(f"[MISSING NAME] index={i}")

    print()
    print(f"Possible conflicts found: {conflicts}")
else:
    print(f"Index not found: {INDEX}")


# ============================================================
# 6. COMPILE
# ============================================================

print()
print("=" * 70)
print("COMPILING")
print("=" * 70)

for path in [LLM, API, STRUCTURED]:
    py_compile.compile(str(path), doraise=True)
    print(f"OK: {path}")

print()
print("=" * 70)
print("PATCH COMPLETE")
print("=" * 70)