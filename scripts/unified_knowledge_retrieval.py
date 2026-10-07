import json
import re
from pathlib import Path

from scripts.structured_product_search import (
    search as product_search,
    get_all_products,
)
from scripts.query_router import route_query

BASE_DIR = Path(__file__).resolve().parent.parent

BUSINESS_FILE = (
    BASE_DIR
    / "05_CANONICAL"
    / "business_knowledge_canonical.json"
)


with BUSINESS_FILE.open(encoding="utf-8") as f:
    business_records = json.load(f)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "").lower().strip()
    )


# ============================================================
# BUSINESS INTENT DETECTION
# ============================================================

def detect_business_intent(query):
    """
    Detect the user's primary business-information intent.

    This does NOT replace normal keyword retrieval.
    It provides an additional relevance boost so that
    highly specific business questions prefer the matching
    knowledge topic.
    """

    q = normalize(query)

    intents = []

    # --------------------------------------------------------
    # RETURN / EXCHANGE
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "return policy",
            "return my",
            "return this",
            "return product",
            "return item",
            "return an item",
            "returns",
            "return",
            "exchange policy",
            "exchange",
            "refund policy",
            "refund",
        ]
    ):
        intents.append("return_exchange_policy")

    # --------------------------------------------------------
    # SHIPPING / DELIVERY
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "shipping policy",
            "shipping",
            "delivery",
            "delivery time",
            "how long does shipping",
            "how long will shipping",
            "how long does delivery",
            "when will my order arrive",
            "when will my order be delivered",
            "delivery time",
            "shipping time",
        ]
    ):
        intents.append("shipping_policy")

    # --------------------------------------------------------
    # ORDER TRACKING
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "track my order",
            "track order",
            "order tracking",
            "tracking my order",
            "where is my order",
            "where's my order",
            "order status",
            "check my order",
            "check order",
        ]
    ):
        intents.append("order_tracking")

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "payment",
            "payments",
            "pay using",
            "pay with",
            "payment method",
            "payment methods",
            "cod",
            "cash on delivery",
            "cash on delivery",
        ]
    ):
        intents.append("payment_methods")

    # --------------------------------------------------------
    # CUSTOMER SUPPORT / CONTACT
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "contact",
            "contact you",
            "contact tones",
            "customer support",
            "customer service",
            "support team",
            "support",
            "email",
            "contact details",
        ]
    ):
        intents.append("customer_support")

    # --------------------------------------------------------
    # ABOUT / BRAND
    # --------------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "about tones",
            "about tones fashion",
            "tell me about tones",
            "what is tones",
            "who are tones",
            "about the brand",
            "about your brand",
            "brand information",
        ]
    ):
        intents.append("brand_identity")

    return intents


# ============================================================
# BUSINESS SEARCH
# ============================================================

def business_search(query, top_k=5):

    q = normalize(query)

    query_words = set(
        re.findall(
            r"\b[a-z0-9]+\b",
            q
        )
    )

    detected_intents = detect_business_intent(q)

    results = []

    for record in business_records:

        facts = record.get(
            "facts",
            []
        )

        facts_text = " ".join(
            str(x)
            for x in facts
        )

        domain = normalize(
            record.get(
                "domain",
                ""
            )
        )

        topic = normalize(
            record.get(
                "topic",
                ""
            )
        )

        title = normalize(
            record.get(
                "title",
                ""
            )
        )

        searchable = " ".join([
            domain,
            topic,
            title,
            normalize(facts_text),
        ])

        score = 0

        # ----------------------------------------------------
        # EXISTING GENERIC MATCHING
        # ----------------------------------------------------

        # Exact topic signal
        if topic and topic in q:
            score += 10

        # Exact domain signal
        if domain and domain in q:
            score += 5

        # Word matching
        for word in query_words:

            if word in title:
                score += 3

            elif word in searchable:
                score += 1

        # ----------------------------------------------------
        # INTENT-BASED BOOSTING
        # ----------------------------------------------------

        for intent in detected_intents:

            # Exact topic match
            if topic == intent:
                score += 15

            # Strong domain/topic relationships
            if intent == "return_exchange_policy":

                if topic == "return_exchange_policy":
                    score += 12

                elif domain == "returns":
                    score += 8

                elif "return" in title:
                    score += 8

                elif "exchange" in title:
                    score += 6

            elif intent == "shipping_policy":

                if topic == "shipping_policy":
                    score += 15

                elif domain == "shipping":
                    score += 8

                elif "shipping" in title:
                    score += 8

                elif "delivery" in title:
                    score += 6

            elif intent == "order_tracking":

                if topic == "order_tracking":
                    score += 15

                elif domain == "orders":
                    score += 8

                elif "track" in title:
                    score += 8

                elif "tracking" in title:
                    score += 8

            elif intent == "payment_methods":

                if topic == "payment_methods":
                    score += 15

                elif domain == "payment":
                    score += 8

                elif "payment" in title:
                    score += 8

            elif intent == "customer_support":

                if topic == "customer_support":
                    score += 15

                elif domain == "business":
                    score += 6

                elif "contact" in title:
                    score += 8

                elif "support" in title:
                    score += 8

            elif intent == "brand_identity":

                if topic == "brand_identity":
                    score += 15

                elif domain == "business":
                    score += 6

                elif "about" in title:
                    score += 8

        # ----------------------------------------------------
        # GENERIC "POLICY" PENALTY
        # ----------------------------------------------------
        #
        # "policy" by itself should not make Privacy Policy,
        # Terms of Service, etc. outrank a specific policy.
        #
        # Example:
        #
        # "what is your return policy"
        #
        # should prefer:
        # Return and Exchange Policy
        #
        # over:
        # Privacy Policy
        # Terms of Service
        #

        if "return_exchange_policy" in detected_intents:

            if topic not in (
                "return_exchange_policy",
            ):
                if domain == "policy":
                    score -= 5

        if "shipping_policy" in detected_intents:

            if topic not in (
                "shipping_policy",
            ):
                if domain == "policy":
                    score -= 5

        if "payment_methods" in detected_intents:

            if topic not in (
                "payment_methods",
            ):
                if domain == "policy":
                    score -= 3

        # ----------------------------------------------------
        # KEEP ONLY RELEVANT RESULTS
        # ----------------------------------------------------

        if score > 0:

            results.append({
                "score": score,
                "record": record,
            })

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# SPECIAL INTENT RETRIEVAL
# ============================================================

def special_intent_retrieve(query, special_intent, product_top_k=10, business_top_k=5):
    """
    Connect the router's specific intent to the existing retrieval
    layer without duplicating canonical business facts.
    """
    product_results = []
    business_results = []

    # Product attribute questions
    if special_intent in ("PRODUCT_FABRIC", "PRODUCT_SIZE"):
        # Generic attribute questions such as:
        # "What is the fabric of the product?"
        # "What sizes are available?"
        # should not return arbitrary products.
        #
        # Only perform product retrieval when the customer query contains
        # enough product-specific information to identify a product.

        attribute_words = {
            "PRODUCT_FABRIC": {
                "fabric", "material", "cloth", "made of", "made from"
            },
            "PRODUCT_SIZE": {
                "size", "sizes", "sizing"
            },
        }

        lowered = query.lower().strip()

        product_reference_terms = (
            " t-shirt ", " tshirt ", " tee ", " shirt ",
            " sweatshirt ", " kurta ", " cargo ",
            " chino ", " jacket ", " product "
        )

        has_product_reference = any(
            term in f" {lowered} "
            for term in product_reference_terms
        )

        # A generic question must not return an arbitrary product.
        generic_product_reference = (
            lowered in {
                "what is the fabric of the product?",
                "what is the fabric of the product",
                "what is the fabric of this product?",
                "what is the fabric of this product",
                "what fabric is the product?",
                "what fabric is the product",
                "what is the material of the product?",
                "what is the material of the product",
                "what sizes are available?",
                "what sizes are available",
                "what sizes are available for the product?",
                "what sizes are available for the product",
                "what sizes does the product have?",
                "what sizes does the product have",
                "product",
                "the product",
                "this product",
                "a product",
            }
        )

        # --------------------------------------------------------
        # NAMED PRODUCT ATTRIBUTE QUERY
        #
        # Example:
        # "What is the fabric of Daily Tees - black?"
        #
        # The product name itself can identify the product even
        # when the query does not contain "tee", "shirt", etc.
        # --------------------------------------------------------

        attribute_prefixes = (
            "what is the fabric of ",
            "what is the material of ",
            "what fabric is ",
            "what material is ",
            "fabric of ",
            "material of ",
            "what sizes are available for ",
            "what sizes does ",
            "sizes for ",
        )

        named_product_query = lowered

        for prefix in attribute_prefixes:
            if named_product_query.startswith(prefix):
                named_product_query = named_product_query[len(prefix):]
                break

        named_product_query = named_product_query.strip(" ?")

        if (
            named_product_query
            and not generic_product_reference
        ):
            try:
                named_filters, named_matches = product_search(
                    named_product_query,
                    top_k=product_top_k,
                )
            except Exception:
                named_filters, named_matches = {}, []

            if named_matches:
                return {
                    "product_results": [
                        {
                            "score": score,
                            "product": product,
                        }
                        for score, product in named_matches
                    ],
                    "business_results": [],
                    "special_operation": "PRODUCT_ATTRIBUTE",
                    "filters": named_filters,
                    "attribute_type": special_intent,
                }

        if not has_product_reference or generic_product_reference:
            return {
                "product_results": [],
                "business_results": [],
                "special_operation": "PRODUCT_ATTRIBUTE_CLARIFICATION",
                "filters": {},
                "attribute_type": special_intent,
            }

        filters, matches = product_search(query, top_k=product_top_k)

        product_results = [
            {"score": score, "product": product}
            for score, product in matches
        ]

        return {
            "product_results": product_results,
            "business_results": [],
            "special_operation": "PRODUCT_ATTRIBUTE",
            "filters": filters,
            "attribute_type": special_intent,
        }

    # Business knowledge questions
    business_intent_map = {
        "RETURN_POLICY": "return_exchange_policy",
        "EXCHANGE_POLICY": "return_exchange_policy",
        "SHIPPING_POLICY": "shipping_policy",
        "ORDER_TRACKING": "order_tracking",
        "ORDER_STATUS": "order_tracking",
        "CONTACT_INFO": "customer_support",
    }

    if special_intent in business_intent_map:
        return {
            "product_results": [],
            "business_results": business_search(query, top_k=business_top_k),
            "special_operation": "BUSINESS_KNOWLEDGE",
            "business_intent": business_intent_map[special_intent],
        }

    # Cancellation: use only whatever verified business knowledge
    # already exists; do not substitute another policy.
    if special_intent == "ORDER_CANCELLATION":
        # Cancellation is already covered by the verified return/exchange
        # knowledge. Reuse that canonical knowledge instead of performing
        # broad business retrieval, which can surface unrelated shipping facts.

        cancellation_results = business_search(
            "cancel order before dispatch",
            top_k=business_top_k,
        )

        filtered = []

        for item in cancellation_results:
            text_blob = str(item).lower()

            if (
                "cancel" in text_blob
                or "dispatch" in text_blob
            ):
                filtered.append(item)

        return {
            "product_results": [],
            "business_results": filtered,
            "special_operation": "BUSINESS_KNOWLEDGE",
            "business_intent": "order_cancellation",
        }

    # Catalogue-wide product aggregation.
    #
    # IMPORTANT:
    # Aggregation questions must NOT use normal top-K retrieval.
    # They must operate over the complete structured catalogue.

    if special_intent in (
        "CHEAPEST_PRODUCT",
        "MOST_EXPENSIVE_PRODUCT",
        "PRODUCTS_ON_SALE",
    ):

        all_products = get_all_products()

        valid_products = []

        for product in all_products:

            if not isinstance(product, dict):
                continue

            try:
                price = float(product.get("price"))
            except (TypeError, ValueError):
                continue

            valid_products.append(
                (price, product)
            )

        # ----------------------------------------------------
        # CHEAPEST PRODUCT
        # ----------------------------------------------------

        if special_intent == "CHEAPEST_PRODUCT":

            if not valid_products:

                matching_products = []

            else:

                minimum_price = min(
                    price
                    for price, _ in valid_products
                )

                matching_products = [
                    product
                    for price, product in valid_products
                    if price == minimum_price
                ]

        # ----------------------------------------------------
        # MOST EXPENSIVE PRODUCT
        # ----------------------------------------------------

        elif special_intent == "MOST_EXPENSIVE_PRODUCT":

            if not valid_products:

                matching_products = []

            else:

                maximum_price = max(
                    price
                    for price, _ in valid_products
                )

                matching_products = [
                    product
                    for price, product in valid_products
                    if price == maximum_price
                ]

        # ----------------------------------------------------
        # PRODUCTS ON SALE
        # ----------------------------------------------------

        else:

            matching_products = []

            for product in all_products:

                if not isinstance(product, dict):
                    continue

                try:
                    price = float(product.get("price"))
                    compare_at_price = float(
                        product.get("compare_at_price")
                    )
                except (TypeError, ValueError):
                    continue

                if compare_at_price > price:

                    matching_products.append(
                        product
                    )

            matching_products.sort(
                key=lambda product: float(
                    product.get("price")
                )
            )

        product_results = [
            {
                "score": 100,
                "product": product,
            }
            for product in matching_products
        ]

        return {
            "product_results": product_results,
            "business_results": [],
            "special_operation": "PRODUCT_AGGREGATION",
            "aggregation_intent": special_intent,
            "filters": {},
        }

    return None


# ============================================================
# UNIFIED RETRIEVAL
# ============================================================

def unified_retrieve(
    query,
    product_top_k=10,
    business_top_k=5,
):

    routing = route_query(query)

    route = routing["route"]
    special_intent = routing.get("special_intent")

    # Specific intents get a dedicated retrieval path first.
    if special_intent:
        special_result = special_intent_retrieve(
            query,
            special_intent,
            product_top_k=product_top_k,
            business_top_k=business_top_k,
        )

        if special_result is not None:
            return {
                "query": query,
                "route": route,
                "special_intent": special_intent,
                "routing": routing,
                "product_results": special_result["product_results"],
                "business_results": special_result["business_results"],
                "special_operation": special_result.get("special_operation"),
                "business_intent": special_result.get("business_intent"),
                "aggregation_intent": special_result.get("aggregation_intent"),
                "filters": special_result.get("filters"),
            }

    product_results = []
    business_results = []

    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    if route in (
        "PRODUCT",
        "MIXED",
    ):

        filters, matches = product_search(
            query,
            top_k=product_top_k
        )

        product_results = [
            {
                "score": score,
                "product": product,
            }
            for score, product in matches
        ]

    # --------------------------------------------------------
    # BUSINESS
    # --------------------------------------------------------

    if route in (
        "BUSINESS",
        "MIXED",
    ):

        business_results = business_search(
            query,
            top_k=business_top_k
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {
        "query": query,

        "route": route,

        "special_intent": special_intent,

        "routing": routing,

        "product_results": product_results,

        "business_results": business_results,
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    queries = [

        "black oversized t shirt",

        "what is your return policy",

        "how long does shipping take",

        "how can I track my order",

        "can I pay using COD",

        "black t shirt and can I return it",

    ]

    print()

    print("=" * 70)

    print(
        "TONES UNIFIED KNOWLEDGE RETRIEVAL"
    )

    print("=" * 70)

    for query in queries:

        result = unified_retrieve(
            query
        )

        print()

        print("=" * 70)

        print(
            "QUERY:",
            query
        )

        print(
            "ROUTE:",
            result["route"]
        )

        print("=" * 70)

        print()

        print(
            "PRODUCT RESULTS"
        )

        if not result["product_results"]:

            print(
                "None"
            )

        else:

            for item in result["product_results"]:

                product = item["product"]

                print(
                    f"{product.get('name')} "
                    f"| Score: {item['score']}"
                )

        print()

        print(
            "BUSINESS RESULTS"
        )

        if not result["business_results"]:

            print(
                "None"
            )

        else:

            for item in result["business_results"]:

                record = item["record"]

                print(
                    f"{record.get('knowledge_id')} "
                    f"| {record.get('topic')} "
                    f"| {record.get('status')} "
                    f"| Score: {item['score']}"
                )