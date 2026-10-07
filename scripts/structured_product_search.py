import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "03_STRUCTURED"
    / "product_search_index.json"
)


with INPUT_FILE.open(encoding="utf-8") as f:
    products = json.load(f)


SIZE_PATTERN = re.compile(
    r"\b(XXL|XL|L|M|S)\b",
    re.IGNORECASE
)


# ============================================================
# PRODUCT TYPE CLASSIFICATION
# ============================================================

PRODUCT_TYPE_RULES = {
    "tshirt": {
        "positive": [
            "t-shirt",
            "t shirt",
            "tshirt",
            "tee",
            "tees",
        ],
        "negative": [
            "shirt",
            "sweatshirt",
            "shacket",
            "kurta",
            "jacket",
            "cargo",
            "chino",
        ],
    },

    "shirt": {
        "positive": [
            "shirt",
            "shacket",
        ],
        "negative": [
            "t-shirt",
            "t shirt",
            "tshirt",
            "tee",
            "tees",
            "sweatshirt",
            "kurta",
            "cargo",
            "chino",
        ],
    },

    "sweatshirt": {
        "positive": [
            "sweatshirt",
            "sweat shirt",
        ],
        "negative": [
            "t-shirt",
            "t shirt",
            "tshirt",
            "tee",
            "shirt",
            "kurta",
            "cargo",
            "chino",
        ],
    },

    "kurta": {
        "positive": [
            "kurta",
            "kurtas",
        ],
        "negative": [],
    },

    "cargo": {
        "positive": [
            "cargo",
            "cargos",
        ],
        "negative": [],
    },

    "chinos": {
        "positive": [
            "chino",
            "chinos",
        ],
        "negative": [],
    },

    "jacket": {
        "positive": [
            "jacket",
        ],
        "negative": [
            "shacket",
        ],
    },
}


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "").lower().strip()
    )


def get_product_text(product):
    """
    Build searchable product text.

    IMPORTANT:
    Product type classification is intentionally handled
    separately from generic relevance matching.
    """

    name = normalize(product.get("name", ""))
    category = normalize(product.get("category", ""))

    collections = " ".join(
        normalize(x)
        for x in product.get("collections", [])
    )

    return f"{name} {category} {collections}".strip()


def classify_product_type(product):
    """
    Return one canonical product type.

    Priority:
    1. Specific product category
    2. Product name
    3. Collections only when the product name gives no
       conflicting/unknown information

    Important:
    Collection membership alone is weak evidence because
    products can belong to promotional, seasonal, sale,
    or broad collections.
    """

    name = normalize(product.get("name", ""))
    category = normalize(product.get("category", ""))

    collections = " ".join(
        normalize(x)
        for x in product.get("collections", [])
    )

    # --------------------------------------------------------
    # Explicit / specific category
    # --------------------------------------------------------

    # Ignore generic Shopify taxonomy such as:
    # "Apparel & Accessories"
    generic_categories = {
        "apparel & accessories",
        "apparel",
        "clothing",
        "products",
    }

    if category and category not in generic_categories:

        if "sweatshirt" in category or "sweat shirt" in category:
            return "sweatshirt"

        if (
            "t-shirt" in category
            or "t shirt" in category
            or "tshirt" in category
        ):
            return "tshirt"

        if "shirt" in category:
            return "shirt"

        if "kurta" in category:
            return "kurta"

        if "cargo" in category:
            return "cargo"

        if "chino" in category:
            return "chinos"

        if "jacket" in category:
            return "jacket"

    # --------------------------------------------------------
    # Product name — strongest product-level evidence
    # --------------------------------------------------------

    # Sweatshirt BEFORE shirt
    if (
        "sweatshirt" in name
        or "sweat shirt" in name
    ):
        return "sweatshirt"

    # T-shirt / tee
    if (
        "t-shirt" in name
        or "t shirt" in name
        or "tshirt" in name
        or re.search(r"\btee\b", name)
        or re.search(r"\btees\b", name)
    ):
        return "tshirt"

    # Shirt / shacket
    if (
        re.search(r"\bshirt\b", name)
        or "shacket" in name
    ):
        return "shirt"

    # Kurta
    if "kurta" in name:
        return "kurta"

    # Cargo
    if "cargo" in name:
        return "cargo"

    # Chino
    if "chino" in name:
        return "chinos"

    # Jacket
    if "jacket" in name:
        return "jacket"

    # --------------------------------------------------------
    # Collections — WEAK evidence
    # --------------------------------------------------------
    #
    # Do NOT classify sweatshirt merely because the product
    # belongs to a sweatshirt collection.
    #
    # This prevents:
    #
    # Tones Original - Black
    # -> collection = sweatshirt
    # -> incorrectly classified as sweatshirt
    #
    # Instead, collection evidence is only used for clearly
    # product-specific collection names.
    # --------------------------------------------------------

    if collections:

        if (
            "t-shirt" in collections
            or "t shirts" in collections
            or "tshirt" in collections
        ):
            return "tshirt"

        if "kurta" in collections:
            return "kurta"

        if "cargo" in collections:
            return "cargo"

        if "chino" in collections:
            return "chinos"

        if "jacket" in collections:
            return "jacket"

    return "unknown"

# ============================================================
# QUERY PARSING
# ============================================================

def parse_query(query):

    q = normalize(query)

    filters = {
        "color": None,
        "fit": None,
        "size": None,
        "max_price": None,
        "min_price": None,
        "product_type": None,
        "availability": None,
    }

    colors = [
        "black",
        "white",
        "grey",
        "gray",
        "red",
        "blue",
        "green",
        "pink",
        "orange",
        "beige",
        "brown",
        "cream",
        "navy",
        "maroon",
    ]

    fits = [
        "oversized",
        "relaxed",
        "regular",
        "slim fit",
    ]

    for color in colors:

        if re.search(
            rf"\b{re.escape(color)}\b",
            q
        ):
            filters["color"] = color
            break

    for fit in fits:

        if fit in q:
            filters["fit"] = fit
            break

    size_match = SIZE_PATTERN.search(q)

    if size_match:
        filters["size"] = size_match.group(1).upper()

    price_match = re.search(
        r"(?:under|below|less than|upto|up to)"
        r"\s*[₹rs.]?\s*([\d,]+)",
        q,
        re.IGNORECASE
    )

    if price_match:
        filters["max_price"] = float(
            price_match.group(1).replace(",", "")
        )

    price_match = re.search(
        r"(?:above|over|more than)"
        r"\s*[₹rs.]?\s*([\d,]+)",
        q,
        re.IGNORECASE
    )

    if price_match:
        filters["min_price"] = float(
            price_match.group(1).replace(",", "")
        )

    if (
        "in stock" in q
        or "in-stock" in q
        or "available" in q
    ):
        filters["availability"] = "IN_STOCK"

    # IMPORTANT:
    # Longer/more-specific phrases first.
    product_types = [
        ("sweatshirts", "sweatshirt"),
        ("sweatshirt", "sweatshirt"),

        ("t-shirts", "tshirt"),
        ("t-shirt", "tshirt"),
        ("t shirts", "tshirt"),
        ("t shirt", "tshirt"),
        ("tees", "tshirt"),
        ("tee", "tshirt"),

        ("shirts", "shirt"),
        ("shirt", "shirt"),

        ("kurtas", "kurta"),
        ("kurta", "kurta"),

        ("cargos", "cargo"),
        ("cargo", "cargo"),

        ("chinos", "chinos"),

        ("jackets", "jacket"),
        ("jacket", "jacket"),
    ]

    for phrase, product_type in product_types:

        if phrase in q:
            filters["product_type"] = product_type
            break

    return filters


# ============================================================
# PRODUCT MATCHING
# ============================================================

def product_matches(product, filters):

    name = normalize(product.get("name", ""))
    color = normalize(product.get("color", ""))
    fit = normalize(product.get("fit", ""))

    # --------------------------------------------------------
    # Color
    # --------------------------------------------------------

    if filters["color"]:

        requested = filters["color"]

        if requested == "gray":
            requested = "grey"

        color_match = requested in color
        name_match = requested in name

        if not color_match and not name_match:
            return False

    # --------------------------------------------------------
    # Fit
    # --------------------------------------------------------

    if filters["fit"]:

        if filters["fit"] not in fit:
            return False

    # --------------------------------------------------------
    # Size
    # --------------------------------------------------------

    if filters["size"]:

        sizes = [
            str(x).upper()
            for x in product.get("sizes", [])
        ]

        if filters["size"] not in sizes:
            return False

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    price = product.get("price")

    if filters["max_price"] is not None:

        if price is None:
            return False

        if float(price) > filters["max_price"]:
            return False

    if filters["min_price"] is not None:

        if price is None:
            return False

        if float(price) < filters["min_price"]:
            return False

    # --------------------------------------------------------
# Availability
# --------------------------------------------------------
    # --------------------------------------------------------
    # Availability
    # --------------------------------------------------------

    if filters["availability"] == "IN_STOCK":

        in_stock_sizes = [
            str(x).upper()
            for x in product.get("in_stock_sizes", [])
        ]

        # If the customer requested a specific size,
        # that exact size must be in stock.
        if filters["size"]:

            if filters["size"] not in in_stock_sizes:
                return False

        # Otherwise, at least one size must be in stock.
        else:

            if not in_stock_sizes:
                return False

    # --------------------------------------------------------
    # STRICT PRODUCT TYPE
    # --------------------------------------------------------

    if filters["product_type"]:

        actual_type = classify_product_type(product)

        if actual_type != filters["product_type"]:
            return False

    return True


# ============================================================
# SCORING
# ============================================================

def calculate_score(query, product, filters):

    query_lower = normalize(query)

    query_words = set(
        re.findall(
            r"\b[a-z0-9]+\b",
            query_lower
        )
    )

    name = normalize(product.get("name", ""))

    score = 0

    # Exact product name
    if query_lower == name:
        score += 30

    # Query phrase appears in product name
    if query_lower in name:
        score += 15

    # Name word matches
    for word in query_words:

        if word in name:
            score += 5

    # Structured filter matches
    if filters["color"]:
        score += 5

    if filters["fit"]:
        score += 5

    if filters["size"]:
        score += 5

    if filters["max_price"] is not None:
        score += 5

    if filters["min_price"] is not None:
        score += 5

    if filters["availability"]:
        score += 5

    # Product type is a strong signal.
    if filters["product_type"]:
        score += 10

    return score


# ============================================================
# PRODUCT AGGREGATION / SALE OPERATIONS
# ============================================================

def _numeric_price(product):
    """Return a valid numeric displayed price, otherwise None."""
    value = product.get("price")
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_cheapest_product(products_list=None):
    """
    Return the product with the lowest validated displayed price.
    This uses the existing structured product records only.
    """
    source_products = products if products_list is None else products_list

    valid = [
        product for product in source_products
        if _numeric_price(product) is not None
    ]

    if not valid:
        return None

    return min(valid, key=_numeric_price)


def get_most_expensive_product(products_list=None):
    """
    Return the product with the highest validated displayed price.
    This uses the existing structured product records only.
    """
    source_products = products if products_list is None else products_list

    valid = [
        product for product in source_products
        if _numeric_price(product) is not None
    ]

    if not valid:
        return None

    return max(valid, key=_numeric_price)


def get_sale_products(products_list=None):
    """
    Return products where both displayed price and compare-at price
    are present and the displayed price is lower.

    We deliberately require both values so a missing compare-at price
    is not treated as a sale.
    """
    source_products = products if products_list is None else products_list
    sale_products = []

    for product in source_products:
        price = _numeric_price(product)

        compare_at = product.get("compare_at_price")
        try:
            compare_at = (
                float(compare_at)
                if compare_at is not None
                else None
            )
        except (TypeError, ValueError):
            compare_at = None

        if (
            price is not None
            and compare_at is not None
            and compare_at > price
        ):
            sale_products.append(product)

    return sorted(
        sale_products,
        key=lambda product: (
            _numeric_price(product),
            normalize(product.get("name", "")),
        ),
    )


# ============================================================
# SEARCH
# ============================================================


# ============================================================
# FULL PRODUCT CATALOGUE ACCESS
# ============================================================

def get_all_products():
    """
    Return the complete structured product catalogue.

    This is used for catalogue-wide operations such as:
    - cheapest product
    - most expensive product
    - products on sale

    Normal customer searches should continue using search().
    """
    return list(products)

def search(query, top_k=10):

    filters = parse_query(query)

    matches = []

    for product in products:

        if not product_matches(
            product,
            filters
        ):
            continue

        score = calculate_score(
            query,
            product,
            filters
        )

        matches.append(
            (
                score,
                product
            )
        )

    matches.sort(
        key=lambda x: (
            -x[0],
            x[1].get("price")
            if x[1].get("price") is not None
            else 999999
        )
    )

    return filters, matches[:top_k]


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":

    queries = [
        "black oversized t shirt",
        "white slim fit t shirt",
        "black t shirts under 1000",
        "XL t shirts",
        "XL t shirts in stock",
        "sweatshirts under 1500",
        "black t shirts in stock",
    ]

    # Aggregation checks
    cheapest = get_cheapest_product()
    expensive = get_most_expensive_product()
    sale_products = get_sale_products()

    print()
    print("=" * 60)
    print("AGGREGATION TESTS")
    print("=" * 60)

    print("CHEAPEST PRODUCT:")
    if cheapest:
        print(
            cheapest.get("name"),
            "| ₹" + str(cheapest.get("price"))
        )
    else:
        print("No valid priced product found")

    print()
    print("MOST EXPENSIVE PRODUCT:")
    if expensive:
        print(
            expensive.get("name"),
            "| ₹" + str(expensive.get("price"))
        )
    else:
        print("No valid priced product found")

    print()
    print("SALE PRODUCTS:", len(sale_products))
    for product in sale_products[:10]:
        print(
            product.get("name"),
            "| ₹" + str(product.get("price")),
            "| Compare at ₹" + str(product.get("compare_at_price"))
        )

    print()
    print("TONES STRICT STRUCTURED PRODUCT SEARCH")
    print("=" * 60)

    for query in queries:

        filters, results = search(query)

        print()
        print("QUERY:", query)
        print("FILTERS:", filters)
        print("-" * 60)

        if not results:
            print("No matching products")
            continue

        for rank, (
            score,
            product
        ) in enumerate(
            results,
            start=1
        ):

            print(
                f"{rank}. "
                f"{product.get('name')} "
                f"| Type: {classify_product_type(product)} "
                f"| ₹{product.get('price')} "
                f"| Sizes: {product.get('sizes')} "
                f"| In stock: {product.get('in_stock_sizes')} "
                f"| Score: {score}"
            )