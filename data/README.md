# Data layers

`tones_7200_qa.json` is retained as **legacy/historical data**. v2 does not use it as the primary answer path.

The current assistant uses:

- `05_CANONICAL/products_enriched.json`
- `05_CANONICAL/reviews_canonical.json`
- `05_CANONICAL/business_knowledge_v2.json`
- `06_RAG/knowledge_documents.jsonl`

Rebuild these with:

```powershell
python scripts/extract_reviews.py
python scripts/build_tones_knowledge.py
```
