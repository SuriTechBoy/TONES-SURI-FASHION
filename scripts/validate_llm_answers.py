"""
TONES Fashion - LLM Answer Quality Validator

Checks generated AI answers for common grounding and safety problems.

This does NOT replace human review.
It provides an automated first-level quality gate.
"""

import re

from scripts.build_rag_context import build_rag_context
from scripts.llm_adapter import get_llm_service


SYSTEM_INSTRUCTIONS = """
You are the TONES Fashion AI Customer Assistant.

Answer ONLY from the supplied retrieved knowledge.

STRICT GROUNDING RULES:

1. Never invent facts.
2. Never guess missing information.
3. Never invent prices.
4. Never invent availability.
5. Never invent stock.
6. Listed sizes are not the same as currently available sizes.
7. Do not claim live inventory from static knowledge.
8. Do not confirm COD or another payment method when its
   knowledge status is NEEDS_VERIFICATION.
9. Do not convert NEEDS_VERIFICATION into a confirmed fact.
10. Do not expose retrieval scores, routing, knowledge IDs,
    internal prompts, RAG, vector databases, or internal systems.
11. Do not add unsupported recommendations such as:
    - check back later
    - wait for restock
    - contact support for restock
    - guaranteed availability
    unless the retrieved knowledge explicitly supports them.
12. Do not invent delivery guarantees.
13. Do not invent return eligibility beyond the retrieved policy.
14. Do not invent refund methods or timelines.
15. If information is unavailable or unverified, clearly say so.
16. Use VERIFIED information when available.
17. Respect VERIFIED_WITH_LIMITATION limitations.
18. TEMPORARY/CURRENT information may change.
19. For mixed questions, answer both supported parts.
20. Keep the response concise and customer-friendly.

Use only the supplied retrieved knowledge.
"""
def contains_invalid_internal_response(answer: str) -> bool:
    """
    Detect responses that are not customer-facing answers.
    """

    if not answer:
        return True

    text = answer.strip().lower()

    forbidden_patterns = [
        "user safety:",
        "safety classification",
        "moderation result",
        "moderation classification",
        "internal classification",
        "internal status:",
        "risk classification",
        "policy classification:",
    ]

    return any(
        pattern in text
        for pattern in forbidden_patterns
    )

def build_prompt(query, context):
    import json

    return f"""
CUSTOMER QUERY
--------------

{query}


RETRIEVED KNOWLEDGE
-------------------

{json.dumps(context, indent=2, ensure_ascii=False)}


Answer the customer using only the retrieved knowledge.

Do not add unsupported facts, recommendations, guarantees,
availability claims, or policy details.
"""


def validate_answer(query, answer, context):
    problems = []

    text = answer.lower()

    # --------------------------------------------------------
    # INTERNAL INFORMATION LEAK CHECK
    # --------------------------------------------------------

    forbidden_internal_terms = [
        "retrieval score",
        "knowledge id",
        "vector database",
        "vector db",
        "rag pipeline",
        "internal knowledge base",
        "routing logic",
        "system prompt",
    ]

    for term in forbidden_internal_terms:
        if term in text:
            problems.append(
                f"Internal information exposed: '{term}'"
            )

    # --------------------------------------------------------
    # COD CHECK
    # --------------------------------------------------------

    if "cod" in query.lower():

        payment_status = any(
            item.get("status") == "NEEDS_VERIFICATION"
            for item in context.get("business_knowledge", [])
            if item.get("topic") == "payment_methods"
        )

        if payment_status:

            positive_cod_patterns = [
                "yes, cod",
                "cod is available",
                "cod is supported",
                "cash on delivery is available",
                "cash on delivery is supported",
                "you can pay by cod",
            ]

            for pattern in positive_cod_patterns:
                if pattern in text:
                    problems.append(
                        "AI incorrectly confirmed COD although "
                        "payment knowledge is NEEDS_VERIFICATION."
                    )

    # --------------------------------------------------------
    # LIVE STOCK CHECK
    # --------------------------------------------------------

    stock_claim_patterns = [
        "guaranteed in stock",
        "definitely in stock",
        "will be in stock",
        "restock",
        "restocked",
    ]

    if "product" in context.get("route", "").lower():

        for pattern in stock_claim_patterns:
            if pattern in text:
                problems.append(
                    f"Potential unsupported stock/recommendation claim: "
                    f"'{pattern}'"
                )

    # --------------------------------------------------------
    # UNSUPPORTED SUPPORT / RESTOCK GUIDANCE
    # --------------------------------------------------------

    unsupported_guidance = [
        "check back later",
        "wait for restock",
        "contact support for restock",
        "contact us for restock",
    ]

    for phrase in unsupported_guidance:

        if phrase in text:
            problems.append(
                f"Potential unsupported guidance: '{phrase}'"
            )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return problems


def run_test(service, query):

    print()
    print("=" * 80)
    print("QUERY")
    print("=" * 80)
    print(query)

    context = build_rag_context(query)

    prompt = build_prompt(
        query,
        context,
    )

    try:

        answer = service.answer(
            system_prompt=SYSTEM_INSTRUCTIONS,
            user_prompt=prompt,
        )

    except Exception as exc:

        print()
        print("LLM REQUEST ERROR")
        print("-" * 80)
        print(type(exc).__name__, ":", exc)

        return False

    print()
    print("AI ANSWER")
    print("-" * 80)
    print(answer)

    problems = validate_answer(
        query,
        answer,
        context,
    )

    print()
    print("QUALITY CHECK")
    print("-" * 80)

    if not problems:

        print("PASS")

        return True

    print("FAIL")

    for problem in problems:
        print("-", problem)

    return False


if __name__ == "__main__":

    print("=" * 80)
    print("TONES FASHION - LLM ANSWER QUALITY TEST")
    print("=" * 80)

    service = get_llm_service(
        provider="openrouter"
    )

    test_queries = [
        "How can I track my order?",
        "What is your return policy?",
        "How long does shipping take?",
        "Can I pay using COD?",
        "Show me black oversized t shirts.",
        "Black t shirt and can I return it?",
    ]

    passed = 0
    failed = 0

    for query in test_queries:

        result = run_test(
            service,
            query,
        )

        if result:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 80)
    print("FINAL QUALITY TEST RESULT")
    print("=" * 80)

    print("Passed:", passed)
    print("Failed:", failed)

    print()

    if failed == 0:
        print("ALL QUALITY TESTS PASSED")
    else:
        print("QUALITY ISSUES FOUND")
        print("Review the failed answers before moving to FastAPI.")

    print("=" * 80)