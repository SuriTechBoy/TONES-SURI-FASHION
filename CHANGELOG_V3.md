# TONES Fashion AI Assistant — V3 Changelog

## V3 goal
Upgrade the existing V2 architecture without replacing the working frontend, catalogue, knowledge base, or API design.

## Core changes
- Added deterministic structured query understanding for product search.
- Multi-condition product filtering now uses hard AND logic.
- Added numeric price ranges: under, below, less than, up to, maximum, between, from/to, and hyphen ranges.
- Added size, availability, rating, gender, fit, fabric/material, style, pattern, occasion, and brand parsing where supported by the catalogue.
- Product type classification was hardened so `T-shirts` cannot be confused with generic `shirts`, and `sweatshirts` cannot be confused with `shirts`.
- Explicit product filters are validated against every returned product before cards are emitted.
- Hard-filtered zero-result queries never fall back to unrelated semantic products.
- Conflicting product color data is treated as unverified; `name_color` cannot override a conflicting verified color field.
- Exact product entity resolution is now checked before broad business/brand routing for product-detail questions.
- Exact product-detail questions return the selected product and its product-specific saved reviews.
- Review retrieval remains entity-sensitive and returns only reviews linked to the resolved product.
- Added customer-friendly out-of-stock/zero-match behavior.
- Added deterministic business routing for location, categories, contact, shipping, returns, payments, ownership, and financial-information questions.
- Added verified Hyderabad business-location and product-category records from the project's verified business knowledge.
- Ownership and financial questions remain non-hallucinatory when public verification is unavailable.
- Nike/smartphone and other unrelated requests now use the friendly out-of-scope path instead of a generic processing error.
- Added lightweight conversation context so follow-ups such as `Only black ones` can inherit previous product filters.
- Frontend now sends a persistent session ID for follow-up context.
- Review text is summarized in the assistant message while detailed reviews remain in review cards, avoiding duplicate review content.
- API version updated to 3.0.0 and health reports `deterministic-strict-hybrid-rag`.

## Validation
- V3 acceptance suite: **33/33 passed (100%)**.
- Legacy 90-question evaluation: **90/90 passed (100%)** after updating the evaluator to treat safe verified zero-result responses as successful product-search behavior.
- FastAPI TestClient smoke tests passed for product search, exact product details, product reviews, business questions, COD uncertainty, out-of-scope requests, and follow-up filtering.

## Known catalogue limitations
- The current 77-product snapshot contains no verified product-level gender field, so men's/women's filters intentionally return a safe no-match/verification response rather than guessing.
- The current snapshot does not contain verified jeans or polo products, so those searches correctly return no verified match.
- Payment methods remain `NEEDS_VERIFICATION`; COD is not asserted as available.
- Inventory is a saved knowledge snapshot, not live Shopify inventory.
