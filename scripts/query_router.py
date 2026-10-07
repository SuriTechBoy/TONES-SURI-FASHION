import re


# ============================================================
# QUERY ROUTER
# ============================================================

PRODUCT_TERMS = [
    "product",
    "products",
    "buy",
    "purchase",
    "price",
    "cost",
    "size",
    "sizes",
    "fit",
    "color",
    "colour",
    "fabric",
    "material",
    "t shirt",
    "t-shirt",
    "tshirt",
    "tee",
    "tees",
    "shirt",
    "shirts",
    "sweatshirt",
    "sweatshirts",
    "kurta",
    "kurtas",
    "cargo",
    "cargos",
    "chino",
    "chinos",
    "jacket",
    "jackets",
    "in stock",
    "available",
    "availability",
    "under ₹",
    "under rs",
    "under ",
    "below ",
]


BUSINESS_TERMS = [
    "return",
    "returns",
    "exchange",
    "refund",
    "refunds",
    "policy",
    "shipping",
    "delivery",
    "deliver",
    "dispatch",
    "track order",
    "tracking",
    "order tracking",
    "order status",
    "cancel order",
    "cancellation",
    "payment",
    "pay",
    "cod",
    "cash on delivery",
    "upi",
    "card",
    "privacy",
    "terms",
    "support",
    "contact",
    "customer service",
    "complaint",
    "damaged",
    "defective",
    "wrong product",
    "about tones",
    "about the brand",
    "brand",
    "company",
]


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "").lower().strip()
    )


def contains_term(query, term):
    """
    Avoid some accidental substring matches.

    Multi-word phrases use direct matching.
    Single words use word boundaries.
    """

    if " " in term or "-" in term:

        return term in query

    return bool(
        re.search(
            rf"\b{re.escape(term)}\b",
            query
        )
    )


# ============================================================
# SPECIAL INTENT DETECTION
# ============================================================

SPECIAL_INTENT_RULES = [
    ("ORDER_STATUS", [
        "what is my order status", "what's my order status",
        "check my order status", "tell me my order status",
        "my order status",
    ]),
    ("ORDER_TRACKING", [
        "track my order", "track order", "order tracking",
        "tracking my order", "where is my order", "where's my order",
    ]),
    ("ORDER_CANCELLATION", [
        "cancel my order", "cancel the order", "cancel an order",
        "can i cancel my order", "can i cancel the order",
        "order cancellation",
    ]),
    ("RETURN_POLICY", [
        "return policy", "can i return", "return a product",
        "return the product", "return an item", "can i return an item",
    ]),
    ("EXCHANGE_POLICY", [
        "exchange policy", "can i exchange", "exchange a product",
        "exchange the product", "exchange an item",
    ]),
    ("CHEAPEST_PRODUCT", [
        "cheapest product", "cheapest item", "lowest price product",
        "lowest priced product", "least expensive product",
        "least expensive item", "what is the cheapest", "what's the cheapest",
    ]),
    ("MOST_EXPENSIVE_PRODUCT", [
        "most expensive product", "most expensive item",
        "highest price product", "highest priced product",
        "costliest product", "costliest item",
    ]),
    ("PRODUCTS_ON_SALE", [
        "products on sale", "product on sale", "items on sale",
        "what is on sale", "what's on sale",
        "which products are on sale", "which items are on sale",
        "sale products",
    ]),
    ("PRODUCT_FABRIC", [
        "what is the fabric", "what's the fabric",
        "what fabric is the product", "what fabric does the product use",
        "fabric of the product", "material of the product",
        "what is the material", "what's the material",
    ]),
    ("PRODUCT_SIZE", [
        "what sizes are available", "which sizes are available",
        "what size is available", "which size is available",
        "available sizes", "what are the sizes", "what sizes do you have",
    ]),
    ("SHIPPING_POLICY", [
        "shipping policy", "shipping", "delivery policy", "delivery time",
        "how long does shipping take", "how long will shipping take",
        "how long does delivery take", "do you deliver",
        "do you deliver across india",
    ]),
    ("CONTACT_INFO", [
        "how can i contact", "how do i contact",
        "contact tones fashion", "contact tones", "contact details",
        "customer support", "customer service",
    ]),
]


def detect_special_intent(query):
    """Detect a specific customer intent without changing existing routes."""
    q = normalize(query)
    for intent, phrases in SPECIAL_INTENT_RULES:
        if any(phrase in q for phrase in phrases):
            return intent
    return None


def route_query(query):

    q = normalize(query)

    product_hits = [
        term
        for term in PRODUCT_TERMS
        if contains_term(q, term)
    ]

    business_hits = [
        term
        for term in BUSINESS_TERMS
        if contains_term(q, term)
    ]

    special_intent = detect_special_intent(q)

    # --------------------------------------------------------
    # Strong business intent
    # --------------------------------------------------------

    strong_business_phrases = [
        "return policy",
        "return my",
        "exchange policy",
        "refund",
        "shipping",
        "delivery",
        "track my order",
        "track order",
        "order tracking",
        "cancel my order",
        "cancellation",
        "cash on delivery",
        "cod",
        "payment",
        "privacy policy",
        "terms of service",
    ]

    if any(
        phrase in q
        for phrase in strong_business_phrases
    ):
        return {
            "route": "BUSINESS",
            "special_intent": special_intent,
            "product_hits": product_hits,
            "business_hits": business_hits,
        }

    # --------------------------------------------------------
    # Product + business mixed query
    # --------------------------------------------------------

    if product_hits and business_hits:

        return {
            "route": "MIXED",
            "special_intent": special_intent,
            "product_hits": product_hits,
            "business_hits": business_hits,
        }

    # --------------------------------------------------------
    # Product
    # --------------------------------------------------------

    if product_hits:

        return {
            "route": "PRODUCT",
            "special_intent": special_intent,
            "product_hits": product_hits,
            "business_hits": business_hits,
        }

    # --------------------------------------------------------
    # Business
    # --------------------------------------------------------

    if business_hits:

        return {
            "route": "BUSINESS",
            "special_intent": special_intent,
            "product_hits": product_hits,
            "business_hits": business_hits,
        }

    # --------------------------------------------------------
    # Unknown / general
    # --------------------------------------------------------

    return {
        "route": "GENERAL",
        "special_intent": special_intent,
        "product_hits": [],
        "business_hits": [],
    }


if __name__ == "__main__":

    queries = [
        "black oversized t shirt",
        "black t shirts under 1000",
        "XL t shirts in stock",
        "sweatshirts under 1500",

        "what is your return policy",
        "how long does shipping take",
        "how can I track my order",
        "can I pay using COD",

        "black t shirt and can I return it",
        "tell me about TONES Fashion",
        "hello",
        "What is the cheapest product you have?",
        "Can I return a product?",
        "Can I exchange a product?",
        "Can I cancel my order?",
        "What is my order status?",
        "Can you track my order?",
        "What is the fabric of the product?",
        "What sizes are available?",
        "Show me products that are on sale",
        "How can I contact TONES Fashion?",
    ]

    print()
    print("TONES QUERY ROUTER")
    print("=" * 60)

    for query in queries:

        result = route_query(query)

        print()
        print("QUERY:", query)
        print("ROUTE:", result["route"])
        print("SPECIAL INTENT:", result.get("special_intent"))
        print(
            "PRODUCT HITS:",
            result["product_hits"]
        )
        print(
            "BUSINESS HITS:",
            result["business_hits"]
        )