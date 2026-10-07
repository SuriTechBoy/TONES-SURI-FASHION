# TONES Fashion AI Assistant — V4 Architecture

## Goal
Build a consistent, grounded commerce assistant using the successful process patterns observed in MRU_AGENT while preserving TONES-specific product and business behavior.

## Core flow

```text
Customer message
      |
      v
Conversation context / deterministic query rewriting
      |
      v
Intent + exact product entity resolution
      |
      +-----------------------+
      |                       |
      v                       v
Product route             Business route
      |                       |
      v                       v
Hard structured filters   Exact business topic selection
      |
      v
Candidate products
      |
      v
Deterministic lexical/reranking pass
      |
      v
Quality / safety gate
      |
      v
Grounded answer formatter
      |
      +---- product cards
      +---- review cards
      +---- business answer
      +---- contextual suggested questions
```

## What was adopted from MRU_AGENT
- Latest-intent-first follow-up handling.
- Standalone query construction for fragmentary follow-ups.
- Strict retrieval before answer generation.
- Quality gates instead of guessing when evidence is weak.
- Dedicated regression/evaluation tests.
- Context-aware suggested questions after answers.

## What remains TONES-specific
- Product/variant structured data is authoritative for product facts.
- Explicit filters are hard constraints: color, product type, price, size, stock, fit, rating, fabric and verified gender.
- Listed sizes and currently recorded in-stock sizes are separate fields.
- Exact product resolution is required for product-specific details and reviews.
- Reviews are retrieved only from the resolved product's review list.
- Business/policy records are selected by verified topic/status.
- Unverified business facts are not invented.
- External/non-TONES requests are explicitly out of scope.

## Important design decision
Qdrant/vector retrieval was not copied into the product-selection path. TONES has structured commerce entities where a hard filter is more authoritative than semantic similarity. Semantic similarity can be added later for long-form business documents, but it must never override hard product constraints.

## Suggested questions
The V4 API returns up to two deterministic, context-aware suggestions. They are generated from the current verified route/entity and do not invent facts.

## Regression status
`evaluation/mru_inspired_regression.py` covers routing, product filtering, exact product resolution, reviews, business safety, out-of-scope behavior, and conversation follow-ups.
