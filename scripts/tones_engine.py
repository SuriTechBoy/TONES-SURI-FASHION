"""TONES Fashion production retrieval engine.

Architecture (inspired by the useful parts of MRU_AGENT):
    query -> intent/entity resolution -> hard filters -> ranking -> quality gate

The LLM is deliberately not the source of truth.  Product facts, stock,
variants, reviews and verified business records are selected deterministically.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from rapidfuzz.fuzz import ratio, token_set_ratio

from scripts.conversation import merge_product_context, standalone_query

BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = BASE_DIR / "05_CANONICAL" / "products_enriched.json"
BUSINESS_FILE = BASE_DIR / "05_CANONICAL" / "business_knowledge_v2.json"

COLORS = [
    "dark red", "light blue", "navy blue", "sky blue", "off white",
    "coffee beige", "golden yellow", "black", "white", "grey", "gray",
    "beige", "brown", "orange", "blue", "navy", "green", "red", "yellow",
    "pink", "maroon", "mustard", "ivory", "khaki", "olive", "cream",
    "purple", "wine", "peach", "sage",
]
PRODUCT_TYPES = {
    "t-shirt": ["t shirt", "t shirts", "t-shirt", "t-shirts", "tshirt", "tshirts", "tee", "tees"],
    "shirt": ["shirt", "shirts", "shacket", "shackets", "overshirt", "overshirts"],
    "sweatshirt": ["sweatshirt", "sweatshirts", "sweater", "sweaters"],
    "kurta": ["kurta", "kurtas"],
    "cargo": ["cargo", "cargos"],
    "chino": ["chino", "chinos"],
    "jeans": ["jeans", "jean"],
    "polo": ["polo", "polos"],
    "dress": ["dress", "dresses"],
    "jacket": ["jacket", "jackets"],
}
GENDERS = {
    "men": ["men", "mens", "men's", "male", "for men", "menswear"],
    "women": ["women", "womens", "women's", "female", "for women", "womenswear"],
}
FIT_TERMS = ["oversized", "relaxed", "regular", "slim fit", "slim", "loose", "boxy", "straight"]
STYLE_TERMS = ["casual", "streetwear", "formal", "minimal", "classic", "everyday", "party", "sporty"]
PATTERN_TERMS = ["striped", "stripe", "printed", "print", "graphic", "floral", "plain", "solid", "acid wash", "washed", "textured"]
OCCASION_TERMS = ["college", "office", "work", "party", "wedding", "vacation", "gym", "everyday", "casual"]
EXTERNAL_TERMS = {
    "nike", "adidas", "puma", "zara", "uniqlo", "h&m", "smartphone", "smartphones",
    "phone", "phones", "laptop", "laptops", "television", "tv", "refrigerator", "car", "cars",
    "cricket", "football", "weather", "joke", "biryani", "python", "calculus", "bitcoin",
    "elon musk", "capital of india",
}


def normalize(text: Any) -> str:
    text = str(text or "").lower().replace("₹", " rs ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def tokens(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z0-9]{2,}\b", normalize(text)))


@lru_cache(maxsize=1)
def load_products() -> list[dict]:
    return json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_business() -> list[dict]:
    return json.loads(BUSINESS_FILE.read_text(encoding="utf-8"))


def product_type(product: dict) -> str:
    name = normalize(product.get("name"))
    category = normalize(product.get("category"))
    ptype = normalize(product.get("product_type"))
    desc = normalize(product.get("description"))
    collections = " ".join(normalize(x.get("collection_url", "")) for x in product.get("collections", []) if isinstance(x, dict))

    if any(re.search(rf"\b{re.escape(x)}\b", name) for x in ["cap", "belt", "wallet", "bag"]):
        return "accessory"
    for source in (ptype, category):
        if not source or source in {"none", "apparel accessories", "apparel", "clothing", "products"}:
            continue
        if re.search(r"\bsweatshirts?\b|\bsweaters?\b", source): return "sweatshirt"
        if re.search(r"\bt[- ]?shirts?\b|\btees?\b", source): return "t-shirt"
        if re.search(r"\bshackets?\b|\bovershirts?\b|\bshirts?\b", source): return "shirt"
        if re.search(r"\bkurtas?\b", source): return "kurta"
        if re.search(r"\bcargos?\b", source): return "cargo"
        if re.search(r"\bchinos?\b", source): return "chino"
        if re.search(r"\bjeans?\b", source): return "jeans"
        if re.search(r"\bpolos?\b", source): return "polo"
        if re.search(r"\bjackets?\b", source): return "jacket"
        if re.search(r"\bdresses?\b", source): return "dress"
    if re.search(r"\b(sweatshirt|sweater)\b", name): return "sweatshirt"
    if re.search(r"\bt[- ]?shirt\b|\btshirt\b|\btee\b", name): return "t-shirt"
    if re.search(r"\bshirt\b|\bshacket\b", name): return "shirt"
    for marker, canonical in [
        ("kurta", "kurta"), ("cargo", "cargo"), ("chino", "chino"),
        ("jeans", "jeans"), ("polo", "polo"), ("jacket", "jacket"), ("dress", "dress"),
    ]:
        if marker in name: return canonical
    if re.search(r"\b(sweatshirt|sweater)\b", desc): return "sweatshirt"
    if re.search(r"\bt[- ]?shirt\b|\btee\b", desc): return "t-shirt"
    if re.search(r"\bshacket\b|\bshirt\b", desc): return "shirt"
    for canonical, markers in {
        "t-shirt": ["/t-shirts", "/tshirts", "/combo-tshirts"],
        "kurta": ["/kurtas"], "cargo": ["/cargo", "/cargos"], "chino": ["/chinos", "/pants"],
        "jeans": ["/jeans"], "polo": ["/polos"], "jacket": ["/jackets"],
    }.items():
        if any(m in collections for m in markers): return canonical
    return "unknown"


def product_text(product: dict) -> str:
    return normalize(" ".join([
        str(product.get("name", "")), str(product.get("color", "")), str(product.get("fit", "")),
        str(product.get("fabric", "")), str(product.get("description", "")), product_type(product),
        " ".join(str(x.get("title", "")) for x in product.get("collections", []) if isinstance(x, dict)),
    ]))


def resolve_product(query: str) -> tuple[dict | None, float]:
    """Resolve only when the query contains a strong product identity.

    Generic questions such as "What sizes are available?" intentionally do not
    fuzzy-match a random catalogue item.
    """
    qn = normalize(query)
    if not qn:
        return None, 0.0
    q_tokens = tokens(qn)
    best, best_score = None, 0.0
    for product in load_products():
        name = normalize(product.get("name")); handle = normalize(product.get("handle"))
        slug = normalize(str(product.get("url", "")).rsplit("/", 1)[-1])
        if name and name in qn:
            return product, 1.0
        name_tokens = tokens(name)
        if len(name_tokens) >= 2 and name_tokens.issubset(q_tokens):
            return product, 0.99
        for c in (handle, slug):
            if c and c in qn and len(c.split()) >= 2:
                return product, 0.98
        # Fuzzy entity resolution is allowed only when the query looks like a
        # product name (two or more meaningful tokens) and is highly similar.
        if len(q_tokens) >= 2:
            score = max(
                [token_set_ratio(qn, c) / 100 for c in (name, handle, slug) if c] or [0.0]
            )
            if score >= 0.88 and score > best_score:
                best, best_score = product, score
    return best, best_score if best_score >= 0.88 else 0.0


def _strip_entity(query: str, entity: dict | None) -> str:
    q = normalize(query)
    if not entity:
        return q
    for raw in [entity.get("name"), entity.get("handle"), str(entity.get("url", "")).rsplit("/", 1)[-1]]:
        r = normalize(raw)
        if r:
            q = re.sub(rf"\b{re.escape(r)}\b", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def extract_price_filter(q: str) -> dict:
    q = normalize(q)
    patterns = [
        r"(?:between|from)\s*(?:rs\s*)?([0-9][0-9,]*)\s*(?:and|to|-)\s*(?:rs\s*)?([0-9][0-9,]*)",
        r"(?:rs\s*)?([0-9][0-9,]*)\s*(?:-|to)\s*(?:rs\s*)?([0-9][0-9,]*)",
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            a, b = float(m.group(1).replace(",", "")), float(m.group(2).replace(",", ""))
            return {"min_price": min(a, b), "max_price": max(a, b)}
    m = re.search(r"(?:under|below|less than|up to|upto|maximum|max|max of|within|at most)\s*(?:rs\s*)?([0-9][0-9,]*)", q)
    if m:
        return {"max_price": float(m.group(1).replace(",", ""))}
    m = re.search(r"(?:above|over|more than|minimum|min of|at least)\s*(?:rs\s*)?([0-9][0-9,]*)", q)
    if m:
        return {"min_price": float(m.group(1).replace(",", ""))}
    return {}


def extract_filters(query: str, entity: dict | None = None) -> dict:
    q = _strip_entity(query, entity)
    filters: dict[str, Any] = {}

    for color in sorted(COLORS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(color)}\b", q):
            filters["color"] = color.title()
            break

    for canonical, variants in PRODUCT_TYPES.items():
        if any(re.search(rf"(?<![a-z]){re.escape(v)}(?![a-z])", q) for v in sorted(variants, key=len, reverse=True)):
            filters["product_type"] = canonical
            break

    for fit in sorted(FIT_TERMS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(fit)}\b", q):
            filters["fit"] = fit
            break

    # Size extraction is deliberately conservative.  Never interpret the 's'
    # in "sizes", "men's" or "women's" as size S.
    size = None
    m = re.search(r"\bsize\b\s*(?:is\s*)?(2xl|xxl|xl|l|m|s|[2-4][0-9])\b", q, re.I)
    if m:
        size = m.group(1).upper()
    if not size:
        m = re.search(r"\b(?:in|with|for)\s+(2xl|xxl|xl|l|m|s|[2-4][0-9])\b", q, re.I)
        if m:
            size = m.group(1).upper()
    if not size:
        m = re.search(r"\b(2xl|xxl|xl|l|m|s)\s+(?:t[- ]?shirts?|tees?|shirts?|sweatshirts?|kurtas?|cargos?|chinos?|jeans|polos?)\b", q, re.I)
        if m:
            size = m.group(1).upper()
    if size:
        filters["size"] = size

    filters.update(extract_price_filter(q))

    rating = re.search(r"(?:rating|ratings|rated)\s*(?:above|over|more than|at least|of)?\s*([1-5](?:\.\d+)?)", q)
    if not rating:
        rating = re.search(r"(?:above|over|more than|at least)\s*([1-5](?:\.\d+)?)\s*(?:rating|ratings|stars?)", q)
    if rating:
        filters["min_rating"] = float(rating.group(1))

    if re.search(r"\b(?:in stock|in-stock|currently available|currently in stock|available in)\b", q):
        filters["availability"] = "IN_STOCK"

    for gender, variants in GENDERS.items():
        if any(re.search(rf"\b{re.escape(v)}\b", q) for v in variants):
            filters["gender"] = gender
            break

    for term in STYLE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", q): filters["style"] = term; break
    for term in PATTERN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", q): filters["pattern"] = term; break
    for term in OCCASION_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", q): filters["occasion"] = term; break

    for fabric in ["pure cotton", "cotton", "linen", "denim", "corduroy", "terry", "french terry", "satin", "lycra", "polyester", "wool"]:
        if re.search(rf"\b{re.escape(fabric)}\b", q): filters["fabric"] = fabric; break

    brand = re.search(r"\b(?:nike|adidas|puma|zara|uniqlo|h&m)\b", q)
    if brand:
        filters["brand"] = brand.group(0)
    return filters


def detect_intent(query: str) -> str:
    q = normalize(query)
    if not q:
        return "UNKNOWN"

    # Explicit external topics always win over broad product words.
    if any(term in q for term in EXTERNAL_TERMS):
        return "OUT_OF_SCOPE"

    entity, conf = resolve_product(q)
    if conf >= 0.96 and any(x in q for x in ["review", "reviews", "customer", "customers", "buyer", "buyers", "quality", "what do people say", "what did customers say", "rating"]):
        return "PRODUCT_REVIEWS"
    if conf >= 0.96 and any(x in q for x in ["tell me about", "tell me everything", "details about", "detail about", "information about", "full details", "everything about"]):
        return "PRODUCT_DETAILS"

    if any(x in q for x in ["reviews", "review", "customer feedback", "what do customers say", "what do buyers think", "what are people saying", "highly rated"]):
        return "PRODUCT_REVIEWS"
    if "rating" in q and not any(x in q for x in ["show me", "find me", "looking for", "recommend", "suggest", "products under", "products below"]):
        return "PRODUCT_REVIEWS"

    if any(x in q for x in ["return", "exchange", "refund", "damaged", "defective", "wrong product"]): return "RETURN_EXCHANGE"
    if any(x in q for x in ["track my order", "track order", "order tracking", "order status", "where is my order", "where's my order"]): return "ORDER_TRACKING"
    if any(x in q for x in ["shipping", "delivery", "dispatch", "arrive", "deliver across", "pan india"]): return "SHIPPING"
    if any(x in q for x in ["cancel my order", "cancel order", "cancellation"]): return "CANCELLATION"
    if any(x in q for x in ["cod", "cash on delivery", "payment method", "payment methods", "pay using", "pay with"]): return "PAYMENTS"
    if any(x in q for x in ["contact", "customer support", "customer service", "support email", "email address"]): return "CONTACT"
    if any(x in q for x in ["cheapest", "least expensive", "lowest price"]): return "CHEAPEST_PRODUCT"
    if any(x in q for x in ["most expensive", "highest price", "costliest"]): return "MOST_EXPENSIVE_PRODUCT"
    if any(x in q for x in ["on sale", "sale products", "discounted products", "offers", "offer", "coupon", "promo"]): return "PRODUCT_OFFERS"

    # Exact product attribute requests.
    attribute_terms = ["fabric", "material", "size", "sizes", "color", "colour", "fit", "available", "availability", "stock", "price", "cost"]
    has_attribute_term = any(re.search(rf"\b{re.escape(x)}\b", q) for x in attribute_terms)
    if entity and conf >= 0.96 and has_attribute_term: return "PRODUCT_ATTRIBUTE"
    if entity and conf >= 0.96 and any(x in q for x in ["is ", "are ", "does ", "do "]): return "PRODUCT_ATTRIBUTE"

    if any(x in q for x in ["show me", "find me", "looking for", "i want", "recommend", "suggest", "products", "t shirts", "shirts", "tees", "sweatshirts", "cargos", "kurtas", "chinos", "jeans", "polos", "dresses", "dress"]):
        return "PRODUCT_SEARCH"
    if has_attribute_term: return "PRODUCT_ATTRIBUTE"
    if any(x in q for x in ["tones", "tones fashion", "brand", "philosophy", "unique", "special", "different", "owner", "founder", "based in", "hyderabad", "categories", "what do you sell"]):
        return "BRAND_BUSINESS"
    return "OUT_OF_SCOPE"


def _verified_color_evidence(product: dict) -> str:
    if product.get("color"):
        return normalize(product.get("color"))
    if product.get("name_color") and not product.get("color_conflict"):
        return normalize(product.get("name_color"))
    desc = str(product.get("description") or "")
    m = re.search(r"\bcolou?rs?\s*[:\-]\s*([^\n\r.]+)", desc, re.I)
    if m:
        return normalize(m.group(1))
    return ""


def _field_contains(text: str, wanted: str) -> bool:
    return normalize(wanted) in normalize(text) if wanted else True


def product_matches(product: dict, filters: dict, query: str = "") -> tuple[bool, float]:
    """Hard-validate every explicit product constraint."""
    score = 0.0
    ptype = product_type(product)
    name = normalize(product.get("name")); fit = normalize(product.get("fit")); desc = normalize(product.get("description"))
    fabric = normalize(product.get("fabric")); searchable = product_text(product)

    if filters.get("brand") and normalize(product.get("brand")) != normalize(filters["brand"]): return False, 0.0
    if filters.get("product_type") and filters["product_type"] != ptype: return False, 0.0

    if filters.get("color"):
        wanted = normalize(filters["color"])
        evidence = _verified_color_evidence(product)
        if product.get("color_conflict"):
            # Conflict records can only match their verified product-level color.
            if wanted != normalize(product.get("color")): return False, 0.0
        elif wanted not in evidence: return False, 0.0
        score += 5

    if filters.get("fit"):
        if normalize(filters["fit"]) not in " ".join([fit, name, desc[:700]]): return False, 0.0
        score += 3
    if filters.get("gender"):
        gender = normalize(product.get("gender"))
        if not gender or filters["gender"] not in gender: return False, 0.0
        score += 4
    if filters.get("size"):
        listed = {str(x).upper() for x in product.get("sizes", [])}
        if filters["size"] not in listed: return False, 0.0
        score += 2
    if filters.get("availability") == "IN_STOCK":
        stock = {str(x).upper() for x in product.get("in_stock_sizes", [])}
        if filters.get("size"):
            if filters["size"] not in stock: return False, 0.0
        elif not stock:
            return False, 0.0
        score += 2
    if filters.get("max_price") is not None:
        if product.get("price") is None or float(product["price"]) > float(filters["max_price"]): return False, 0.0
        score += 2
    if filters.get("min_price") is not None:
        if product.get("price") is None or float(product["price"]) < float(filters["min_price"]): return False, 0.0
        score += 2
    if filters.get("min_rating") is not None:
        rating = (product.get("review_summary") or {}).get("average_rating")
        if rating is None or float(rating) < float(filters["min_rating"]): return False, 0.0
        score += 1
    if filters.get("fabric") and not _field_contains(fabric, filters["fabric"]): return False, 0.0
    if filters.get("style") and not _field_contains(searchable, filters["style"]): return False, 0.0
    if filters.get("pattern") and not _field_contains(searchable, filters["pattern"]): return False, 0.0
    # Occasion is a preference unless the catalogue contains an explicit
    # occasion field; never fabricate a hard match.
    if filters.get("occasion"):
        if filters["occasion"] in searchable: score += 0.5
    if query:
        overlap = len(tokens(query) & tokens(searchable)) / max(1, len(tokens(query)))
        score += min(2.0, overlap * 2.0)
    return True, score


def _rank_products(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    q = normalize(query)
    ranked = []
    for p in candidates:
        text = product_text(p)
        lexical = token_set_ratio(q, text) / 100
        name_score = token_set_ratio(q, normalize(p.get("name"))) / 100 if p.get("name") else 0
        price = float(p.get("price")) if p.get("price") is not None else 10**9
        score = lexical * 2 + name_score * 3
        ranked.append((score, -price, normalize(p.get("name")), p))
    ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
    return [x[3] for x in ranked[:top_k]]


def structured_product_search(query: str, top_k: int = 8, filters: dict | None = None) -> list[dict]:
    filters = dict(filters if filters is not None else extract_filters(query))
    candidates = []
    for product in load_products():
        ok, score = product_matches(product, filters, query)
        if ok:
            candidates.append((score, product))
    candidates.sort(key=lambda x: (-x[0], normalize(x[1].get("name"))))
    # A second lexical pass makes results stable when many products satisfy the
    # same hard constraints.
    return _rank_products(query, [p for _, p in candidates], top_k)


def review_search(query: str, top_k: int = 8) -> tuple[dict | None, float, list[dict]]:
    product, confidence = resolve_product(query)
    if not product or confidence < 0.96:
        return None, confidence, []
    reviews = sorted(product.get("reviews", []), key=lambda r: str(r.get("date") or ""), reverse=True)
    return product, confidence, reviews[:top_k]


def business_search(query: str, top_k: int = 3) -> list[dict]:
    q = normalize(query)
    records = load_business()
    explicit = None
    if any(x in q for x in ["owner", "owns", "owned by", "founder"]): explicit = "ownership"
    elif any(x in q for x in ["profit", "revenue", "income"]): explicit = "financial_information"
    elif any(x in q for x in ["hyderabad", "based in", "where is tones"]): explicit = "business_location"
    elif any(x in q for x in ["categories", "what do you sell", "what products do you sell"]): explicit = "product_categories"
    elif any(x in q for x in ["contact", "email", "customer support", "support email"]): explicit = "customer_support"
    elif any(x in q for x in ["track", "where is my order"]): explicit = "order_tracking"
    elif any(x in q for x in ["shipping", "delivery", "deliver", "dispatch"]): explicit = "shipping_policy"
    elif any(x in q for x in ["return", "exchange", "refund", "damaged", "defective"]): explicit = "return_exchange_policy"
    elif any(x in q for x in ["cod", "payment", "pay"]): explicit = "payment_methods"
    elif any(x in q for x in ["offer", "coupon", "promo", "discount"]): explicit = "current_promotions"
    elif any(x in q for x in ["about", "what is tones", "what kind of brand", "what does tones stand"]): explicit = "brand_identity"
    elif any(x in q for x in ["why choose", "special", "different", "unique", "focus on indian men"]): explicit = "brand_differentiation"
    if explicit:
        exact = [r for r in records if r.get("topic") == explicit]
        if exact:
            return exact[:top_k]
    qt = tokens(q)
    scored = []
    for record in records:
        text = tokens(" ".join([str(record.get("title", "")), str(record.get("topic", "")), *[str(x) for x in record.get("facts", [])]]))
        scored.append((len(qt & text), record))
    scored.sort(key=lambda x: -x[0])
    return [r for score, r in scored[:top_k] if score > 0]


def _has_unsupported_gender(filters: dict) -> bool:
    return bool(filters.get("gender")) and not any(p.get("gender") for p in load_products())


def _needs_budget_clarification(query: str, filters: dict) -> bool:
    q = normalize(query)
    return "budget" in q and "max_price" not in filters and "min_price" not in filters


def is_tones_related(query: str, intent: str) -> bool:
    q = normalize(query)
    if intent == "OUT_OF_SCOPE": return False
    if any(term in q for term in EXTERNAL_TERMS): return False
    return intent in {
        "PRODUCT_SEARCH", "PRODUCT_ATTRIBUTE", "PRODUCT_DETAILS", "PRODUCT_REVIEWS",
        "CHEAPEST_PRODUCT", "MOST_EXPENSIVE_PRODUCT", "PRODUCT_OFFERS", "BRAND_BUSINESS",
        "RETURN_EXCHANGE", "SHIPPING", "ORDER_TRACKING", "CANCELLATION", "PAYMENTS", "CONTACT",
    }


def retrieve(query: str, top_k: int = 8, context: dict | None = None) -> dict:
    original_query = str(query or "").strip()
    standalone = standalone_query(original_query, context)
    intent = detect_intent(original_query)
    entity, entity_conf = resolve_product(original_query)

    # If the latest turn is a short follow-up, use the latest clear intent from
    # the previous turn rather than treating the fragment as a new topic.
    qn = normalize(original_query)
    followup = bool(context and len(qn.split()) <= 8 and any(
        marker in qn for marker in ["only ", "just ", "these", "those", "ones", "what about", "which", "under ", "below ", "above ", "in xl", "in l", "in m", "in s"]
    ))
    if context and followup and intent == "OUT_OF_SCOPE":
        previous_intent = context.get("intent") or "PRODUCT_SEARCH"
        if previous_intent in {"PRODUCT_SEARCH", "PRODUCT_ATTRIBUTE", "PRODUCT_DETAILS", "PRODUCT_REVIEWS"}:
            intent = previous_intent

    filters = extract_filters(original_query, entity if entity_conf >= 0.96 else None)
    exact_entity = entity_conf >= 0.96
    if intent in {"PRODUCT_SEARCH", "PRODUCT_ATTRIBUTE"}:
        filters = merge_product_context(filters, context, exact_entity=exact_entity)

    result = {
        "query": original_query,
        "standalone_query": standalone,
        "intent": intent,
        "route": "TONES" if is_tones_related(original_query, intent) else "OUT_OF_SCOPE",
        "filters": filters,
        "product": None,
        "products": [],
        "reviews": [],
        "business": [],
        "entity_confidence": 0.0,
        "needs_clarification": False,
        "unsupported_gender_filter": _has_unsupported_gender(filters),
    }
    if result["route"] == "OUT_OF_SCOPE":
        return result

    if _needs_budget_clarification(original_query, filters):
        result["needs_clarification"] = True
        result["clarification_reason"] = "budget_amount_missing"
        return result

    if intent == "PRODUCT_REVIEWS":
        # A generic review question can inherit the exact product from context.
        p = entity if exact_entity else (context or {}).get("product")
        if p:
            reviews = sorted(p.get("reviews", []), key=lambda r: str(r.get("date") or ""), reverse=True)[:top_k]
            result.update({"product": p, "reviews": reviews, "entity_confidence": 1.0 if p is (context or {}).get("product") else entity_conf})
        return result

    if intent in {"BRAND_BUSINESS", "RETURN_EXCHANGE", "SHIPPING", "ORDER_TRACKING", "CANCELLATION", "PAYMENTS", "CONTACT"}:
        result["business"] = business_search(original_query, 3)
        return result

    if intent == "PRODUCT_DETAILS":
        p = entity if exact_entity else (context or {}).get("product")
        if p:
            result.update({"product": p, "entity_confidence": 1.0 if p is (context or {}).get("product") else entity_conf})
            result["reviews"] = sorted(p.get("reviews", []), key=lambda r: str(r.get("date") or ""), reverse=True)[:top_k]
        else:
            result["needs_clarification"] = True
        return result

    if intent == "PRODUCT_ATTRIBUTE":
        p = entity if exact_entity else (context or {}).get("product")
        if p:
            result.update({"product": p, "entity_confidence": 1.0 if p is (context or {}).get("product") else entity_conf})
        else:
            result["needs_clarification"] = True
        return result

    if intent == "CHEAPEST_PRODUCT":
        candidates = [p for p in load_products() if p.get("price") is not None]
        if candidates:
            minimum = min(float(p["price"]) for p in candidates)
            result["products"] = [p for p in candidates if float(p["price"]) == minimum]
        return result

    if intent == "MOST_EXPENSIVE_PRODUCT":
        candidates = [p for p in load_products() if p.get("price") is not None]
        if candidates:
            maximum = max(float(p["price"]) for p in candidates)
            result["products"] = [p for p in candidates if float(p["price"]) == maximum]
        return result

    if intent == "PRODUCT_OFFERS":
        result["products"] = [
            p for p in load_products()
            if p.get("compare_at_price") is not None and p.get("price") is not None
            and float(p["compare_at_price"]) > float(p["price"])
        ][:top_k]
        result["business"] = business_search(original_query, 2)
        return result

    # Product search / browse.
    if exact_entity:
        ok, _ = product_matches(entity, filters, original_query)
        if ok:
            result.update({"product": entity, "products": [entity], "entity_confidence": entity_conf})
        else:
            # Explicit product + conflicting filter => zero results. Never substitute.
            result["entity_confidence"] = entity_conf
        return result

    result["products"] = structured_product_search(standalone, top_k, filters)
    return result
