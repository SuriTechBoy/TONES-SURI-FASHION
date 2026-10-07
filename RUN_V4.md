# TONES Fashion V4 — Run Guide

## Backend (Windows PowerShell)

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected engine:

```text
mru-inspired-deterministic-hybrid-rag
```

## Frontend

Open a second PowerShell terminal:

```powershell
cd .\frontend
npm.cmd install
npm.cmd run dev
```

Then open the Vite URL shown by the terminal, normally:

```text
http://localhost:5173
```

## Evaluation

From the project root:

```powershell
.\.venv\Scripts\python.exe evaluation\v3_acceptance.py
.\.venv\Scripts\python.exe evaluation\mru_inspired_regression.py
```

The final V4 regression target is:

```text
41 / 41 passed
```

## Important behavior

- Product selection is deterministic and hard-filtered.
- Exact product questions resolve one product before reviews/details are returned.
- `listed_sizes` and `currently_in_stock_sizes` are different facts.
- Unverified gender constraints do not produce substitute products.
- Unsupported/external topics are refused cleanly.
- Business questions use the verified business knowledge records.
- Follow-up questions can inherit the latest product/search context through `session_id`.
- Each answer can return up to two contextual suggested questions.
