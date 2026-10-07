from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

from scripts.tones_engine import retrieve, load_products, load_business
from scripts.answer_generator import generate

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_INDEX_FILE = BASE_DIR / "03_STRUCTURED" / "product_image_index.json"
try:
    IMAGE_INDEX = json.loads(IMAGE_INDEX_FILE.read_text(encoding="utf-8"))
except Exception:
    IMAGE_INDEX = {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("tones-api")

app = FastAPI(
    title="TONES Fashion AI Assistant API",
    description="Grounded deterministic hybrid retrieval assistant for TONES Fashion",
    version="4.0.0",
)

SESSION_STATE: dict[str, dict] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001", "http://localhost:5173",
        "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default=None, max_length=100)


class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    product_id: str
    name: str
    url: str
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    currency: Optional[str] = None
    color: Optional[str] = None
    name_color: Optional[str] = None
    color_conflict: bool = False
    fit: Optional[str] = None
    fabric: Optional[str] = None
    listed_sizes: list[str] = []
    currently_in_stock_sizes: list[str] = []
    image_url: Optional[str] = None
    average_rating: Optional[float] = None
    review_count: int = 0


class ReviewResponse(BaseModel):
    review_id: str
    product_id: str
    product_name: str
    rating: Optional[int] = None
    author: str
    body: str
    date: Optional[str] = None
    verified_buyer: bool = False
    source_url: Optional[str] = None


class BusinessResponse(BaseModel):
    knowledge_id: str
    topic: str
    title: str
    status: str
    facts: list[str] = []
    source_url: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    route: str
    intent: str
    response_type: str
    session_id: Optional[str] = None
    products: list[ProductResponse] = []
    reviews: list[ReviewResponse] = []
    business: list[BusinessResponse] = []
    suggested_questions: list[str] = []


def image_for(product_id: str) -> Optional[str]:
    record = IMAGE_INDEX.get(str(product_id)) if isinstance(IMAGE_INDEX, dict) else None
    return record.get("image_url") if isinstance(record, dict) else None


def product_response(product: dict) -> ProductResponse:
    summary = product.get("review_summary") or {}
    return ProductResponse(
        product_id=str(product.get("product_id", "")),
        name=str(product.get("name", "")),
        url=str(product.get("url", "")),
        price=product.get("price"),
        compare_at_price=product.get("compare_at_price"),
        currency=product.get("currency", "INR"),
        color=product.get("color"),
        name_color=product.get("name_color"),
        color_conflict=bool(product.get("color_conflict")),
        fit=product.get("fit"),
        fabric=product.get("fabric"),
        listed_sizes=[str(x) for x in product.get("sizes", []) if x],
        currently_in_stock_sizes=[str(x) for x in product.get("in_stock_sizes", []) if x],
        image_url=image_for(str(product.get("product_id"))),
        average_rating=summary.get("average_rating"),
        review_count=int(summary.get("review_count") or 0),
    )


def review_response(review: dict) -> ReviewResponse:
    return ReviewResponse(
        review_id=str(review.get("review_id", "")),
        product_id=str(review.get("product_id", "")),
        product_name=str(review.get("product_name", "")),
        rating=review.get("rating"),
        author=str(review.get("author") or "Anonymous"),
        body=str(review.get("body") or ""),
        date=review.get("date"),
        verified_buyer=bool(review.get("verified_buyer")),
        source_url=review.get("source_url"),
    )


def business_response(record: dict) -> BusinessResponse:
    return BusinessResponse(
        knowledge_id=str(record.get("knowledge_id", "")),
        topic=str(record.get("topic", "")),
        title=str(record.get("title", "")),
        status=str(record.get("status", "")),
        facts=[str(x) for x in record.get("facts", [])],
        source_url=record.get("source_url"),
    )


@app.get("/")
def root():
    return {"status": "online", "service": "TONES Fashion AI Assistant", "version": "4.0.0"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "engine": "mru-inspired-deterministic-hybrid-rag",
        "version": "4.0.0",
        "products": len(load_products()),
        "business_records": len(load_business()),
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        session_id = request.session_id or str(uuid4())
        previous = SESSION_STATE.get(session_id)
        retrieval = retrieve(message, context=previous)
        generated = generate(retrieval)

        # Exact entity resolution is authoritative. Once the retrieval layer
        # identifies one product with high confidence, never let a downstream
        # generator broaden the product-card payload with unrelated matches.
        exact_product = retrieval.get("product")
        exact_confidence = float(retrieval.get("entity_confidence") or 0.0)

        products = generated.get("products") or []

        if (
            exact_product
            and exact_confidence >= 0.96
            and retrieval.get("intent") in {"PRODUCT_SEARCH", "PRODUCT_ATTRIBUTE"}
        ):
            products = [exact_product]
        elif not products and exact_product and generated.get("response_type") == "product":
            products = [exact_product]

        response = ChatResponse(
            answer=generated["answer"],
            route=retrieval.get("route", "TONES"),
            intent=retrieval.get("intent", "UNKNOWN"),
            response_type=generated.get("response_type", "text"),
            session_id=session_id,
            products=[product_response(p) for p in products if p.get("name") and p.get("url")],
            reviews=[review_response(r) for r in generated.get("reviews", [])],
            business=[business_response(b) for b in generated.get("business", [])],
            suggested_questions=[str(q) for q in generated.get("suggested_questions", []) if str(q).strip()][:2],
        )
        SESSION_STATE[session_id] = {
            "filters": retrieval.get("filters", {}),
            "product_ids": [p.get("product_id") for p in retrieval.get("products", []) if p.get("product_id")],
            "product": retrieval.get("product"),
            "intent": retrieval.get("intent"),
            "query": message,
            "suggested_questions": response.suggested_questions,
        }
        logger.info("query=%r intent=%s response_type=%s products=%d reviews=%d", message, response.intent, response.response_type, len(response.products), len(response.reviews))
        return response
    except Exception as exc:
        logger.exception("Chat failure: %s", exc)
        raise HTTPException(status_code=500, detail="The TONES AI assistant could not process this request.") from exc


@app.post("/api/v1/retrieve")
def retrieve_debug(request: ChatRequest):
    """Developer/evaluation endpoint. Not intended as the customer UI response."""
    return retrieve(request.message.strip())
