TONES Fashion — Intent → Existing Knowledge → Answer Library v0.1

Purpose

Reuse existing verified TONES knowledge instead of creating a separate factual answer for every wording variation.

Core flow

Customer wording → Intent → Existing canonical knowledge → Customer answer

The answer library is not a replacement for the canonical knowledge base. It tells the router which existing knowledge record to use and how to respond.

Important rules

Reuse verified knowledge.

Do not invent missing facts.

Do not attach unrelated product cards to policy/business questions.

For a product attribute question without a product name, ask for the product name.

Do not claim live inventory from the static knowledge snapshot.

For aggregation questions such as “cheapest”, use a structured database operation instead of generic top-K retrieval.

For “on sale”, only use sale logic when both displayed price and compare-at/original price are available and validated.

Initial mappings

Intent

Existing knowledge / operation

Product cards?

RETURN_POLICY

TONES-KB-RETURNS-001

No

EXCHANGE_POLICY

TONES-KB-RETURNS-001

No

ORDER_CANCELLATION

TONES-KB-RETURNS-001 + relevant TONES-KB-SHIPPING-001 fact

No

SHIPPING_POLICY

TONES-KB-SHIPPING-001

No

ORDER_TRACKING

TONES-KB-ORDER-TRACKING-001

No

ORDER_STATUS

TONES-KB-ORDER-TRACKING-001 + no live-status claim

No

CONTACT_INFO

TONES-KB-CONTACT-001

No

PRODUCT_FABRIC

Existing product fabric field

Only after product identified

PRODUCT_SIZE

Existing product variant_sizes / recorded stock fields

Only after product identified

CHEAPEST_PRODUCT

MIN(price) over validated product records

No generic top-K

MOST_EXPENSIVE_PRODUCT

MAX(price) over validated product records

No generic top-K

PRODUCTS_UNDER_PRICE

Structured price filter

Yes

PRODUCTS_ON_SALE

compare_at_price > displayed_price, only when validated

Yes

PRODUCT_SEARCH

Existing structured product retrieval

Yes

Examples

Return

All of these should map to RETURN_POLICY:

Can I return a product?

What is your return policy?

Can I send the product back?

Is return available?

They reuse TONES-KB-RETURNS-001.

Exchange

All of these should map to EXCHANGE_POLICY:

Can I exchange a product?

What is your exchange policy?

Can I exchange this?

They reuse TONES-KB-RETURNS-001.

Cancellation

“Can I cancel my order?” should not retrieve generic shipping information. It should select the specific cancellation fact from the existing verified policy knowledge.

Fabric

“What is the fabric?” has no product reference, so the system should ask:

Which product are you asking about? Please give me the product name, and I can check its recorded fabric information.

Once the product is identified, reuse that product's canonical fabric field.

Cheapest

“What is the cheapest product you have?” must not use the normal top-K product search.

It should execute:

MIN(validated product price)

and return the product(s) at that price.

Source-derived knowledge IDs currently reused

TONES-KB-RETURNS-001 — Return and Exchange Policy

TONES-KB-SHIPPING-001 — Shipping and Delivery Policy

TONES-KB-ORDER-TRACKING-001 — Track Order

TONES-KB-CONTACT-001 — Customer Support Contact

The source material also specifies canonical product fields including product ID, name, product type, displayed price, compare-at price, availability, variant sizes, fit, fabric, colour, care instructions, return restriction, source URL, verification status, confidence, and conflict flags