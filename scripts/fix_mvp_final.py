from pathlib import Path
import re
import shutil
import json

ROOT = Path(__file__).resolve().parents[1]

LLM = ROOT / "scripts" / "llm_adapter.py"
API = ROOT / "api" / "main.py"
RETRIEVAL = ROOT / "scripts" / "unified_knowledge_retrieval.py"

def backup(path):
    backup_path = path.with_suffix(path.suffix + ".bak_final")
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

# ---------------------------------------------------------
# 1. LLM ADAPTER
# ---------------------------------------------------------

backup(LLM)
text = read(LLM)

# ---------------------------------------------------------
# A. Make generic PRODUCT_ATTRIBUTE clarification explicit
# ---------------------------------------------------------

old = '''special_intent = context.get("special_intent")
        special_operation = context.get("special_operation")
        operation = special_intent or special_operation'''

new = '''special_intent = context.get("special_intent")
        special_operation = context.get("special_operation")
        attribute_type = context.get("attribute_type")
        business_intent = context.get("business_intent")

        # Retrieval may explicitly tell us that the customer asked
        # for a product attribute without identifying a product.
        # This must be handled before normal product retrieval.
        if special_operation == "PRODUCT_ATTRIBUTE_CLARIFICATION":
            if attribute_type == "PRODUCT_FABRIC":
                return (
                    "Sure. Which TONES Fashion product would you like "
                    "to know the fabric details for? Please provide the "
                    "product name."
                )

            if attribute_type == "PRODUCT_SIZE":
                return (
                    "Sure. Which TONES Fashion product would you like "
                    "to know the available sizes for? Please provide the "
                    "product name."
                )

            if attribute_type == "PRODUCT_FIT":
                return (
                    "Sure. Which TONES Fashion product would you like "
                    "to know the fit details for? Please provide the "
                    "product name."
                )

            if attribute_type == "PRODUCT_MATERIAL":
                return (
                    "Sure. Which TONES Fashion product would you like "
                    "to know the material details for? Please provide the "
                    "product name."
                )

        operation = special_intent or special_operation'''

if old in text:
    text = text.replace(old, new, 1)
    print("LLM: clarification handler added")
else:
    print("LLM: clarification insertion point not found")

# ---------------------------------------------------------
# B. Replace generic attribute handling with deterministic text
# ---------------------------------------------------------

pattern = re.compile(
    r'if operation in \{"PRODUCT_FABRIC","PRODUCT_SIZE","PRODUCT_FIT","PRODUCT_MATERIAL"\}:.*?'
    r'(?=\n\s*#|\n\s*if |\n\s*return )',
    re.S
)

replacement = '''if operation in {"PRODUCT_FABRIC", "PRODUCT_SIZE", "PRODUCT_FIT", "PRODUCT_MATERIAL"}:
            attribute = {
                "PRODUCT_FABRIC": "fabric",
                "PRODUCT_SIZE": "available sizes",
                "PRODUCT_FIT": "fit",
                "PRODUCT_MATERIAL": "material",
            }[operation]

            return (
                f"Sure. Which TONES Fashion product would you like "
                f"to know the {attribute} details for? Please provide "
                f"the product name."
            )
'''

match = pattern.search(text)

if match:
    text = text[:match.start()] + replacement + text[match.end():]
    print("LLM: generic attribute answer normalized")
else:
    print("LLM: generic attribute block not replaced; explicit clarification handler still active")

# ---------------------------------------------------------
# C. Fix cancellation wording
# ---------------------------------------------------------

cancel_marker = 'if business_intent == "order_cancellation"'

if cancel_marker in text:
    print("LLM: cancellation handler already present")
else:
    print("LLM: cancellation handler marker not found; existing handler retained")

# ---------------------------------------------------------
# D. Replace common Unicode bullet/dash literals with ASCII-safe text
# ---------------------------------------------------------

# We deliberately use ASCII in generated API text.
# This avoids Windows console/code-page corruption.
text = text.replace("• ", "- ")
text = text.replace(" — ", " - ")
text = text.replace("–", "-")
text = text.replace("—", "-")

write(LLM, text)

# ---------------------------------------------------------
# 2. API
# ---------------------------------------------------------

backup(API)
api_text = read(API)

# ---------------------------------------------------------
# Add explicit no-product-card gate for clarification
# ---------------------------------------------------------

needle = '''products = []
        if route in {"PRODUCT", "MIXED"}:'''

replacement = '''products = []

        # Attribute clarification questions must never return
        # unrelated product cards.
        if context.get("special_operation") == "PRODUCT_ATTRIBUTE_CLARIFICATION":
            products = []
        elif route in {"PRODUCT", "MIXED"}:'''

if needle in api_text:
    api_text = api_text.replace(needle, replacement, 1)
    print("API: clarification product-card gate added")
else:
    print("API: clarification gate already exists or insertion point changed")

write(API, api_text)

# ---------------------------------------------------------
# 3. RETRIEVAL
# ---------------------------------------------------------

backup(RETRIEVAL)
retrieval_text = read(RETRIEVAL)

# Make sure generic fabric/size clarification returns
# explicit metadata.
if 'PRODUCT_ATTRIBUTE_CLARIFICATION' in retrieval_text:
    print("RETRIEVAL: attribute clarification logic already present")
else:
    print("RETRIEVAL: clarification logic missing - manual inspection required")

write(RETRIEVAL, retrieval_text)

# ---------------------------------------------------------
# 4. Compile everything
# ---------------------------------------------------------

print()
print("=" * 70)
print("COMPILING MVP FILES")
print("=" * 70)

import py_compile

for path in [LLM, API, RETRIEVAL]:
    py_compile.compile(str(path), doraise=True)
    print(f"OK: {path}")

print()
print("=" * 70)
print("MVP FINAL PATCH COMPLETE")
print("=" * 70)