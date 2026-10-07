# TONES Fashion AI Assistant V3 — Run Guide

## Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected engine:

```text
deterministic-strict-hybrid-rag
```

Expected version:

```text
3.0.0
```

## Frontend

Open a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open the Vite Local URL, normally:

```text
http://localhost:5173/
```

## Developer retrieval endpoint

`POST /api/v1/retrieve`

Use it to inspect intent, filters, entity resolution and product results.

## API chat endpoint

`POST /api/v1/chat`

Example body:

```json
{
  "message": "Show me black oversized T-shirts under ₹1200 in XL",
  "session_id": "demo-session"
}
```

## Important behavior

- Product selection is deterministic and catalogue-grounded.
- All explicit product conditions are ANDed.
- Zero matches never fall back to unrelated products.
- Product-specific reviews are linked by product entity.
- Verified business knowledge is separate from product retrieval.
- Unknown TONES facts are not invented.
- Unrelated questions are politely redirected.
- Follow-up product filters can reuse the session's previous filters.
