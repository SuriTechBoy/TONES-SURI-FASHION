# TONES Fashion AI Assistant v2 — Change Log

## Major changes

### Retrieval
- Removed the 7,200 Q&A file from the primary chat path.
- Added deterministic intent routing.
- Added product/entity resolution with fuzzy matching and anti-substitution safeguards.
- Added structured product filtering for color, fit, type, size and price.
- Added TF-IDF hybrid retrieval over product/business/review documents.
- Added exact product → review retrieval.
- Added out-of-scope routing.

### Knowledge
- Added `products_enriched.json`.
- Added `reviews_canonical.json` extracted from saved Judge.me product-page HTML.
- Added review summaries and product/review relationships.
- Added `business_knowledge_v2.json`.
- Added brand differentiation, promotion, ownership-boundary and financial-boundary knowledge.
- Preserved source URLs and verification statuses.

### Answers
- Added deterministic grounded answer generation.
- Generic attribute questions now ask for a product instead of returning random products.
- Unknown product/review queries do not silently substitute another product.
- Ownership/profit questions return a verified-information boundary instead of hallucinating.
- Current promotions are treated as temporary/current.

### UI/API
- API response now exposes `intent`, `response_type`, `products`, `reviews`, and `business`.
- Added product review cards to React.
- Existing product cards continue to work.

### Evaluation
- Added a 90-question evaluation suite.
- Current deterministic evaluation: **90/90 passed (100%)**.

## Important limitation

The bundled knowledge is a September 2026 local snapshot of the official TONES pages supplied in the project. The live TONES website changes, and the current website can contain products that are not in this snapshot. Use `scripts/refresh_knowledge.py` on an internet-connected machine and revalidate before promoting a refreshed snapshot.
