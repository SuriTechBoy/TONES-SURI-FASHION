from scripts.unified_knowledge_retrieval import unified_retrieve

def format_product(product_result):
    product = product_result.get(
        "product",
        {}
    )

    return {
        "type": "product",

        # Product ID is inside the product object
        "product_id": product.get(
            "product_id"
        ),

        "title": product.get(
            "name"
        ),

        "url": product.get(
            "url"
        ),

        "price": product.get(
            "price"
        ),

        "currency": product.get(
            "currency"
        ),

        "color": product.get(
            "color"
        ),

        "fit": product.get(
            "fit"
        ),

        "fabric": product.get(
            "fabric"
        ),

        "sizes": product.get(
            "sizes",
            []
        ),

        "in_stock_sizes": product.get(
            "in_stock_sizes",
            []
        ),

        "score": product_result.get(
            "score"
        ),
    }


def format_business(business_result):
    record = business_result.get(
        "record",
        {}
    )

    return {
        "type": "business",

        "knowledge_id": record.get(
            "knowledge_id"
        ),

        "domain": record.get(
            "domain"
        ),

        "topic": record.get(
            "topic"
        ),

        "title": record.get(
            "title"
        ),

        "status": record.get(
            "status"
        ),

        "source_url": record.get(
            "source_url"
        ),

        "source_type": record.get(
            "source_type"
        ),

        "collected_at": record.get(
            "collected_at"
        ),

        "facts": record.get(
            "facts",
            []
        ),

        "score": business_result.get(
            "score"
        ),
    }


def build_rag_context(
    query,
    product_top_k=5,
    business_top_k=5
):

    retrieval = unified_retrieve(
        query,
        product_top_k=product_top_k,
        business_top_k=business_top_k,
    )

    # --------------------------------------------------------
    # UNIFIED RETRIEVAL STRUCTURE
    # --------------------------------------------------------

    product_results = retrieval.get(
        "product_results",
        []
    )

    business_results = retrieval.get(
        "business_results",
        []
    )

    products = [
        format_product(item)
        for item in product_results
    ]

    business = [
        format_business(item)
        for item in business_results
    ]

    context = {
        "query": query,

        "route": retrieval.get(
            "route"
        ),

        "products": products,

        "business_knowledge": business,

        "rules": {
            "do_not_invent_information": True,

            "verified_statuses": [
                "VERIFIED",
                "VERIFIED_WITH_LIMITATION",
            ],

            "restricted_statuses": [
                "NEEDS_VERIFICATION",
            ],

            "temporary_statuses": [
                "TEMPORARY/CURRENT",
            ],

            "size_vs_stock_rule":
                "A listed size does not mean that "
                "the size is currently in stock.",

            "live_inventory_rule":
                "Current live inventory must eventually "
                "come from a live store/inventory source.",
        },
    }

    return context


def print_context(context):

    print()
    print("=" * 80)
    print("RAG CONTEXT")
    print("=" * 80)
    print()

    print("QUERY:")
    print(
        context["query"]
    )

    print()

    print("ROUTE:")
    print(
        context.get(
            "route"
        )
    )

    print()

    print("PRODUCT KNOWLEDGE:")

    if not context["products"]:
        print(
            "No product results"
        )

    for product in context["products"]:

        print("-" * 60)

        print(
            "Product ID:",
            product["product_id"]
        )

        print(
            "Title:",
            product["title"]
        )

        print(
            "Price:",
            product["price"],
            product["currency"]
        )

        print(
            "Color:",
            product["color"]
        )

        print(
            "Fit:",
            product["fit"]
        )

        print(
            "Fabric:",
            product["fabric"]
        )

        print(
            "Sizes:",
            product["sizes"]
        )

        print(
            "In stock sizes:",
            product["in_stock_sizes"]
        )

        print(
            "Score:",
            product["score"]
        )

    print()

    print("BUSINESS KNOWLEDGE:")

    if not context["business_knowledge"]:
        print(
            "No business knowledge results"
        )

    for item in context["business_knowledge"]:

        print("-" * 60)

        print(
            "ID:",
            item["knowledge_id"]
        )

        print(
            "Title:",
            item["title"]
        )

        print(
            "Domain:",
            item["domain"]
        )

        print(
            "Topic:",
            item["topic"]
        )

        print(
            "Status:",
            item["status"]
        )

        print(
            "Source:",
            item["source_url"]
        )

        print(
            "Score:",
            item["score"]
        )

        print(
            "Facts:"
        )

        for fact in item["facts"]:
            print(
                " -",
                fact
            )

    print()

    print("RAG RULES:")

    print(
        context["rules"]
    )


if __name__ == "__main__":

    queries = [
        "black oversized t shirt",
        "what is your return policy",
        "how long does shipping take",
        "how can I track my order",
        "can I pay using COD",
    ]

    for query in queries:

        context = build_rag_context(
            query
        )

        print_context(
            context
        )