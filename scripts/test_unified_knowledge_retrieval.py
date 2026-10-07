from unified_knowledge_retrieval import unified_retrieve


def product_names(result):

    return [
        item["product"].get("name", "")
        for item in result["product_results"]
    ]


def business_ids(result):

    return [
        item["record"].get("knowledge_id", "")
        for item in result["business_results"]
    ]


def assert_true(condition, message):

    if not condition:
        raise AssertionError(
            f"FAIL: {message}"
        )

    print(
        f"PASS: {message}"
    )


# ============================================================
# 1. PRODUCT ROUTING
# ============================================================

result = unified_retrieve(
    "black oversized t shirt"
)

assert_true(
    result["route"] == "PRODUCT",
    "product query routed to PRODUCT"
)

assert_true(
    len(result["business_results"]) == 0,
    "product query has no business results"
)


# ============================================================
# 2. STRICT T-SHIRT FILTERING
# ============================================================

names = product_names(result)

for name in names:

    assert_true(
        "shirt" not in name.lower()
        or "t-shirt" in name.lower()
        or "t shirt" in name.lower(),
        f"T-shirt result is not an ordinary shirt: {name}"
    )

    assert_true(
        "sweatshirt" not in name.lower(),
        f"T-shirt result is not a sweatshirt: {name}"
    )


# Explicit known leakage checks
assert_true(
    "BLACK DOUBLE POCKET FLANNEL   SHIRT" not in names,
    "flannel shirt excluded from T-shirt search"
)

assert_true(
    "Jet Black - Satin Shirt" not in names,
    "satin shirt excluded from T-shirt search"
)

assert_true(
    "Pink Oxford Shirt" not in names,
    "Oxford shirt excluded from T-shirt search"
)


# ============================================================
# 3. BLACK T-SHIRTS UNDER ₹1000
# ============================================================

result = unified_retrieve(
    "black t shirts under 1000"
)

assert_true(
    result["route"] == "PRODUCT",
    "black T-shirt price query routed to PRODUCT"
)

names = product_names(result)

assert_true(
    len(result["business_results"]) == 0,
    "product price query has no business results"
)

for item in result["product_results"]:

    product = item["product"]

    assert_true(
        float(product["price"]) <= 1000,
        f"price filter respected: {product.get('name')}"
    )


# ============================================================
# 4. T-SHIRT AVAILABILITY
# ============================================================

result = unified_retrieve(
    "XL t shirts in stock"
)

assert_true(
    result["route"] == "PRODUCT",
    "availability query routed to PRODUCT"
)

for item in result["product_results"]:

    product = item["product"]

    assert_true(
        "XL" in [
            str(x).upper()
            for x in product.get("in_stock_sizes", [])
        ],
        f"XL is actually in stock for: {product.get('name')}"
    )

    assert_true(
        "shirt" not in product.get(
            "name",
            ""
        ).lower()
        or "t-shirt" in product.get(
            "name",
            ""
        ).lower()
        or "t shirt" in product.get(
            "name",
            ""
        ).lower(),
        f"XL result is a T-shirt: {product.get('name')}"
    )


# ============================================================
# 5. SWEATSHIRT STRICT FILTER
# ============================================================

result = unified_retrieve(
    "sweatshirts under 1500"
)

assert_true(
    result["route"] == "PRODUCT",
    "sweatshirt query routed to PRODUCT"
)

names = product_names(result)

assert_true(
    "Tones Original - Black" not in names,
    "Tones Original excluded from sweatshirt search"
)

for name in names:

    assert_true(
        "sweatshirt" in name.lower(),
        f"sweatshirt result is actually a sweatshirt: {name}"
    )


# ============================================================
# 6. RETURN POLICY ROUTING
# ============================================================

result = unified_retrieve(
    "what is your return policy"
)

assert_true(
    result["route"] == "BUSINESS",
    "return-policy query routed to BUSINESS"
)

assert_true(
    len(result["product_results"]) == 0,
    "return-policy query has no product results"
)

assert_true(
    "TONES-KB-RETURNS-001"
    in business_ids(result),
    "return policy retrieved"
)


# ============================================================
# 7. SHIPPING ROUTING
# ============================================================

result = unified_retrieve(
    "how long does shipping take"
)

assert_true(
    result["route"] == "BUSINESS",
    "shipping query routed to BUSINESS"
)

assert_true(
    len(result["product_results"]) == 0,
    "shipping query has no product results"
)

assert_true(
    "TONES-KB-SHIPPING-001"
    in business_ids(result),
    "shipping policy retrieved"
)


# ============================================================
# 8. ORDER TRACKING ROUTING
# ============================================================

result = unified_retrieve(
    "how can I track my order"
)

assert_true(
    result["route"] == "BUSINESS",
    "order-tracking query routed to BUSINESS"
)

assert_true(
    len(result["product_results"]) == 0,
    "order-tracking query has no product results"
)

assert_true(
    "TONES-KB-ORDER-TRACKING-001"
    in business_ids(result),
    "order tracking knowledge retrieved"
)


# ============================================================
# 9. PAYMENT / COD
# ============================================================

result = unified_retrieve(
    "can I pay using COD"
)

assert_true(
    result["route"] == "BUSINESS",
    "COD query routed to BUSINESS"
)

assert_true(
    len(result["product_results"]) == 0,
    "COD query has no product results"
)

payment_records = [
    item["record"]
    for item in result["business_results"]
    if item["record"].get("knowledge_id")
    == "TONES-KB-PAYMENT-001"
]

assert_true(
    len(payment_records) == 1,
    "payment knowledge retrieved"
)

assert_true(
    payment_records[0].get("status")
    == "NEEDS_VERIFICATION",
    "COD uncertainty remains NEEDS_VERIFICATION"
)


# ============================================================
# 10. MIXED QUERY
# ============================================================

result = unified_retrieve(
    "Can I return the black T-shirt?"
)

assert_true(
    result["route"] == "MIXED",
    "mixed product + return query routed to MIXED"
)

assert_true(
    len(result["product_results"]) > 0,
    "mixed query retrieves products"
)

assert_true(
    "TONES-KB-RETURNS-001"
    in business_ids(result),
    "mixed query retrieves return policy"
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 70)
print("ALL QUERY ROUTER + STRICT PRODUCT RETRIEVAL TESTS PASSED")
print("=" * 70)