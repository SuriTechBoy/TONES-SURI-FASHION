from structured_product_search import search


def unified_product_search(query, top_k=5):

    filters, matches = search(
        query,
        top_k=top_k
    )

    results = []

    for score, product in matches:

        product_id = (
            product.get("product_id")
            or product.get("id")
            or product.get("handle")
            or product.get("url")
            or product.get("name")
        )

        results.append(
            {
                "product_id": product_id,
                "score": score,
                "product": product,
                "filters": filters,
            }
        )

    return results


if __name__ == "__main__":

    queries = [
        "black oversized t shirt",
        "white slim fit t shirt",
        "XL t shirts in stock",
        "sweatshirt under 1500",
    ]

    print()
    print("TONES UNIFIED PRODUCT RETRIEVAL")
    print("=" * 70)

    for query in queries:

        print()
        print("QUERY:", query)
        print("-" * 70)

        results = unified_product_search(
            query,
            top_k=5
        )

        if not results:

            print("No matching products")
            continue

        for rank, result in enumerate(
            results,
            start=1
        ):

            product = result["product"]

            print(
                f"{rank}. "
                f"{product.get('name')} "
                f"| ₹{product.get('price')} "
                f"| Color: {product.get('color')} "
                f"| Fit: {product.get('fit')} "
                f"| In stock: {product.get('in_stock_sizes')} "
                f"| Score: {result.get('score')}"
            )