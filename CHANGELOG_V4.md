# TONES Fashion AI Assistant — V4 Changelog

## MRU-inspired consistency upgrade

### Backend
- Reworked `scripts/tones_engine.py` around explicit intent/entity resolution, hard filters, deterministic ranking and quality gates.
- Added deterministic conversation handling in `scripts/conversation.py`.
- Added contextual suggested questions in `scripts/suggestions.py`.
- Strengthened exact product resolution so generic questions cannot randomly bind to a product.
- Fixed size parsing so `sizes` no longer becomes size `S`.
- Fixed intent detection so words such as `oversized` do not accidentally trigger the `size` attribute route.
- Preserved strict variant-level stock checks.
- Preserved exact product-specific review retrieval.
- Preserved safe handling of missing/verified business information.
- Added budget clarification when a user says "my budget" without specifying an amount.
- Added session intent/product context for MRU-style follow-up behavior.
- API version is now 4.0.0.

### Frontend
- Existing TONES visual/frontend structure is preserved.
- Added per-answer contextual suggested-question chips using the existing suggestion styling.
- Initial welcome suggestions remain unchanged.
- Product/review cards remain unchanged.

### Evaluation
- Added `evaluation/mru_inspired_regression.py`.
- Final regression run: **41/41 passed (100%)**.
- Existing V3 acceptance suite: **33/33 passed (100%)**.

### Validation note
The frontend dependency install/build could not be completed inside the Linux build container because package installation timed out. The source change itself is limited to adding the `suggestedQuestions` response field and rendering those chips; run `npm.cmd install` and `npm.cmd run build` in the user's Windows project environment before deployment.
