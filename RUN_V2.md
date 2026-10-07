# TONES Fashion AI Assistant v2

## What changed

The old 7,200-question lookup is no longer the primary answer path.

The v2 assistant uses a deterministic-first hybrid retrieval pipeline:

1. Query understanding and intent detection
2. Product/entity resolution
3. Structured product filtering
4. TF-IDF semantic/keyword retrieval over TONES knowledge documents
5. Product → review relationship retrieval
6. Verified business knowledge retrieval
7. Grounded response generation
8. Structured response types for React cards
9. Out-of-scope guard
10. Evaluation suite

The 7,200 Q&A file is preserved as historical material only.

## Current local knowledge snapshot

Generated from the uploaded repository snapshot:

- 77 products
- 188 product reviews across 63 products
- 16 business/brand knowledge records
- 281 retrieval documents

The live TONES website changes, so this snapshot must be refreshed periodically.

## Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

Test:

```text
http://127.0.0.1:8000/health
```

Chat endpoint:

```text
POST http://127.0.0.1:8000/api/v1/chat
```

## Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Important

The frontend `node_modules` folder is intentionally not part of the deliverable. Run `npm install` on the target laptop.

## Knowledge rebuild

After changing source data:

```powershell
python scripts/extract_reviews.py
python scripts/build_tones_knowledge.py
python evaluation/run_evaluation.py
```

## Live refresh

On an internet-connected machine:

```powershell
python scripts/refresh_knowledge.py
```

This creates a separate live HTML snapshot. Review the new data before promoting it into the canonical snapshot.

## Evaluation

Run:

```powershell
python evaluation/run_evaluation.py
```

The test suite currently contains 90 questions covering:

- Product discovery
- Product attributes
- Product reviews
- Brand/business questions
- Shipping
- Returns/exchanges
- Orders/tracking
- Out-of-scope questions

## Accuracy principle

If a fact is not present and verified, the assistant must say it does not have a verified answer. It must not guess ownership, profit, COD availability, inventory, or other unsupported facts.


### Windows Application Control note
This v2 backend no longer requires scikit-learn/numpy/scipy for retrieval. The retrieval engine uses a lightweight pure-Python TF-IDF implementation, avoiding native DLLs that may be blocked by Windows Application Control.
