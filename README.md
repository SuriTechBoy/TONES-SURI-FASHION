# TONES Fashion AI Assistant — v3

A grounded AI shopping assistant for TONES Fashion.

## v3 architecture

```text
Customer question
      ↓
Intent + entity understanding
      ↓
TONES / out-of-scope guard
      ↓
┌─────────────────────────────────────────────┐
│ Product structured retrieval                 │
│ Product/entity resolution                    │
│ Product → review retrieval                   │
│ TF-IDF hybrid knowledge retrieval             │
│ Verified business knowledge                  │
└─────────────────────────────────────────────┘
      ↓
Grounded response generator
      ↓
Product / product-list / review / business card
```

### Important change

The old `data/tones_7200_qa.json` dataset is **not used as the primary retrieval path**. It is retained only as historical material.

The assistant now answers TONES product and website questions from structured/canonical knowledge and product-specific review data. V3 adds strict multi-condition filtering, deterministic intent routing, exact product-detail handling, safe zero-result behavior, business-topic routing, and follow-up context. Brand/business questions use a separate verified business knowledge layer. Unrelated questions receive a TONES scope response.

## Current snapshot

Generated from the uploaded project snapshot:

- **77 products**
- **188 product reviews** across **63 products**
- **16 business/brand knowledge records**
- **281 retrieval documents**
- **90 legacy evaluation questions**
- **33 V3 acceptance tests**
- Current local evaluation: **90/90 legacy passed (100%)** and **33/33 V3 acceptance passed (100%)**

The knowledge is a snapshot. TONES is a live Shopify store, so refresh and revalidate the knowledge periodically.

## Run backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Run frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The Vite development proxy sends `/api` requests to the FastAPI server on port 8000.

## Rebuild local knowledge

```powershell
python scripts/extract_reviews.py
python scripts/build_tones_knowledge.py
python evaluation/run_evaluation.py
```

## Refresh from the live website

On an internet-connected machine:

```powershell
python scripts/refresh_knowledge.py
```

Review the newly collected live snapshot before promoting it into canonical knowledge.

## API

### Chat

`POST /api/v1/chat`

```json
{"message":"What are the reviews for Tones Original Black T-Shirt?"}
```

The response includes:

- `answer`
- `intent`
- `response_type`
- `products`
- `reviews`
- `business`

### Developer retrieval inspection

`POST /api/v1/retrieve`

This exposes the retrieval decision for evaluation/debugging and should not be treated as the customer-facing response.

## Accuracy rules

The assistant must not invent:

- product prices
- inventory
- sizes
- reviews
- ownership
- profit/revenue
- payment methods that are unverified
- any other unsupported TONES fact

If the knowledge base does not contain a verified answer, the assistant says so rather than substituting a guess or a different product.

## Main files

- `scripts/tones_engine.py` — routing, entity resolution and retrieval
- `scripts/answer_generator.py` — grounded customer responses
- `scripts/extract_reviews.py` — Judge.me review extraction from saved product pages
- `scripts/build_tones_knowledge.py` — builds enriched canonical/RAG data
- `scripts/refresh_knowledge.py` — live website refresh helper
- `api/main.py` — FastAPI API
- `frontend/src/App.jsx` — chat UI and product/review cards
- `evaluation/` — automated retrieval/response evaluation

See `RUN_V3.md` for setup and workflow details. See `CHANGELOG_V3.md` for the V3 implementation and validation details.
