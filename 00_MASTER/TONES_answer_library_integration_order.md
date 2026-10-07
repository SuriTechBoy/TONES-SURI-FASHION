Integration order

Add the answer-library module to scripts/.

Run it directly to verify intent detection.

Update the existing query router so these special intents are checked BEFORE generic PRODUCT/BUSINESS/MIXED classification.

When a special business intent is selected, do not attach generic product results.

For CHEAPEST_PRODUCT / MOST_EXPENSIVE_PRODUCT, perform a structured MIN/MAX over validated product prices.

For PRODUCT_FABRIC / PRODUCT_SIZE, ask for a product name when none is present; do not return random products.

Re-run the 24-question MVP test.

Add new regression tests for every intent and several alternate wordings.