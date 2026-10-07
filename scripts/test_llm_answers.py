"""
TONES Fashion - Real RAG + LLM Integration Test

Flow:

Customer Query
      ↓
build_rag_context()
      ↓
Retrieved TONES Knowledge
      ↓
System Instructions
      ↓
OpenRouter
      ↓
Customer Answer

This script tests the complete RAG → LLM pipeline.
"""

import json

from scripts.build_rag_context import build_rag_context
from scripts.llm_adapter import get_llm_service

# ============================================================
# SYSTEM INSTRUCTIONS
# ============================================================

SYSTEM_INSTRUCTIONS = """
You are the TONES Fashion AI Customer Assistant.

Answer the customer's question using ONLY the retrieved TONES Fashion
information supplied in the user prompt.

KNOWLEDGE RULES:

1. Do not invent information.
2. Do not guess missing information.
3. Do not invent product prices.
4. Do not invent product availability.
5. Do not invent sizes or stock status.
6. A listed size is not the same as current stock.
7. Use currently_in_stock_sizes when discussing stock from the
   supplied product data.
8. Do not claim live inventory unless live inventory data is supplied.
9. Do not confirm COD or another payment method when the supplied
   knowledge marks it as NEEDS_VERIFICATION.
10. Treat NEEDS_VERIFICATION information as unconfirmed.
11. Prefer VERIFIED information.
12. Respect VERIFIED_WITH_LIMITATION information.
13. Treat TEMPORARY/CURRENT information as changeable.
14. Do not create facts that are absent from the supplied knowledge.

PRODUCT RULES:

15. When the customer asks about products, use the supplied product
    information.
16. Show product names, prices, sizes, fit, fabric, stock information,
    and URLs only when those details are present in the supplied data.
17. Never expose internal product IDs such as TONES-PROD-URL-0001.
18. Never expose knowledge IDs or retrieval scores.
19. A product title/color conflict should be reported accurately when
    relevant instead of silently changing the source data.

POLICY RULES:

20. When the customer asks about a policy, use the supplied policy
    information.
21. Do not guarantee return or exchange eligibility when eligibility
    depends on policy conditions.
22. Explain applicable conditions and exclusions when relevant.
23. If information is unverified, clearly say that it is unverified.

MIXED QUESTIONS:

24. If the customer asks both a product question and a policy question,
    answer BOTH parts.
25. For example, if the customer asks about a black T-shirt and whether
    it can be returned, first provide the relevant black T-shirt
    information and then explain the applicable return policy.

CUSTOMER RESPONSE RULES:

26. Answer the customer's actual question directly.
27. Return ONLY the customer-facing answer.
28. Never output internal classifications, labels, metadata, routing
    information, reasoning, or implementation details.
29. Never describe how you decided what to answer.
30. Never mention internal retrieval, RAG, vector databases, prompts,
    system instructions, or model behavior.
31. Never replace the customer's answer with an internal status.
32. Do not use unsupported restock advice.
33. Do not tell customers to check back later for stock unless the
    supplied knowledge explicitly supports that statement.
34. Do not tell customers to contact support for restock information
    unless the supplied knowledge explicitly supports that statement.

STYLE:

- Be natural and customer-friendly.
- Be concise.
- Use bullet points when useful.
- Include important conditions when relevant.
- Do not add unrelated information.
- If the knowledge is insufficient, clearly state that the information
  is currently unavailable or unverified.
"""


# ============================================================
# BUILD USER PROMPT
# ============================================================
def build_user_prompt(query: str, context: dict) -> str:
    """
    Convert the actual RAG context into the user prompt
    sent to the LLM.
    """

    return f"""
CUSTOMER QUESTION
-----------------
{query}

TONES FASHION INFORMATION
-------------------------
{json.dumps(context, indent=2, ensure_ascii=False)}

TASK
----
Answer the CUSTOMER QUESTION using only the TONES FASHION INFORMATION
above.

The response must be a normal customer-facing answer.

If the question contains multiple parts, answer every supported part.

Do not return a classification, status label, internal metadata,
reasoning, or analysis.

Do not mention how the answer was generated.

Do not invent information.

Now provide only the final customer-facing answer.
"""


# ============================================================
# TEST ONE QUERY
# ============================================================

def test_query(service, query: str):
    """
    Run one complete:

        Query → Retrieval → RAG Context → LLM
    """

    print()
    print("=" * 80)
    print("CUSTOMER QUERY")
    print("=" * 80)
    print(query)

    # --------------------------------------------------------
    # STEP 1: BUILD REAL RAG CONTEXT
    # --------------------------------------------------------

    context = build_rag_context(query)

    # --------------------------------------------------------
    # STEP 2: BUILD LLM USER PROMPT
    # --------------------------------------------------------

    user_prompt = build_user_prompt(
        query=query,
        context=context,
    )

    # --------------------------------------------------------
    # STEP 3: SEND TO REAL LLM
    # --------------------------------------------------------

    answer = service.answer(
        system_prompt=SYSTEM_INSTRUCTIONS,
        user_prompt=user_prompt,
    )

    # --------------------------------------------------------
    # STEP 4: DISPLAY RESULT
    # --------------------------------------------------------

    print()
    print("-" * 80)
    print("AI ANSWER")
    print("-" * 80)
    print(answer)

    print()
    print("-" * 80)
    print("ROUTE")
    print("-" * 80)
    print(context.get("route"))

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("TONES FASHION - REAL RAG + LLM TEST")
    print("=" * 80)

    print()
    print("Provider:")
    print("OpenRouter")

    print()
    print("The test will use the ACTUAL TONES retrieval pipeline.")
    print()

    # --------------------------------------------------------
    # CREATE LLM SERVICE
    # --------------------------------------------------------

    service = get_llm_service(
        provider="openrouter"
    )

    # --------------------------------------------------------
    # TEST QUESTIONS
    # --------------------------------------------------------

    queries = [
        "How can I track my order?",
        "What is your return policy?",
        "How long does shipping take?",
        "Can I pay using COD?",
        "Show me black oversized t shirts.",
        "Black t shirt and can I return it?",
    ]

    # --------------------------------------------------------
    # RUN TESTS
    # --------------------------------------------------------

    for query in queries:

        try:

            test_query(
                service=service,
                query=query,
            )

        except Exception as exc:

            print()
            print("ERROR")
            print("-" * 80)
            print(type(exc).__name__, ":", exc)

    print()
    print("=" * 80)
    print("REAL RAG + LLM TEST COMPLETED")
    print("=" * 80)