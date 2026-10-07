from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

QA_PATH = Path(__file__).resolve().parent.parent / "data" / "tones_7200_qa.json"


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("₹", " rs ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> set[str]:
    return set(_normalize(text).split())


def load_qa() -> list[dict[str, str]]:
    if not QA_PATH.exists():
        return []
    with QA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [x for x in data if isinstance(x, dict) and x.get("question") and x.get("answer")]


_QA = load_qa()
_EXACT = {_normalize(x["question"]): x for x in _QA}


def find_qa_answer(query: str, fuzzy: bool = True) -> dict[str, Any] | None:
    """Return a grounded answer from the 7,200-question dataset.

    Exact normalized matches are authoritative. Fuzzy matching is only used
    when the query is very close to a stored customer question.
    """
    normalized = _normalize(query)
    if not normalized:
        return None

    exact = _EXACT.get(normalized)
    if exact:
        return {"answer": exact["answer"], "question": exact["question"], "score": 1.0, "match_type": "exact"}

    if not fuzzy:
        return None

    query_tokens = _tokens(query)
    if not query_tokens:
        return None

    best = None
    best_score = 0.0
    for item in _QA:
        candidate = item["question"]
        cand_norm = _normalize(candidate)
        seq = SequenceMatcher(None, normalized, cand_norm).ratio()
        cand_tokens = _tokens(candidate)
        union = query_tokens | cand_tokens
        jaccard = len(query_tokens & cand_tokens) / len(union) if union else 0.0
        score = 0.70 * seq + 0.30 * jaccard
        if score > best_score:
            best_score = score
            best = item

    # High threshold prevents unrelated questions from being answered from
    # the dataset.
    if best is not None and best_score >= 0.91:
        return {"answer": best["answer"], "question": best["question"], "score": round(best_score, 4), "match_type": "fuzzy"}

    return None


def qa_dataset_size() -> int:
    return len(_QA)
