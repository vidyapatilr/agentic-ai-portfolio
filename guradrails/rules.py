import re


def check_rules(response: str, tool_results: list[dict]) -> dict:
    violations = []

    # Rule 1: No PII — block credit card numbers in output
    if re.search(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", response):
        violations.append("PII detected: credit card number in response")

    # Rule 2: Refund amount must never exceed order amount
    for result in tool_results:
        if result.get("eligible") and result.get("amount"):
            if result["amount"] > 1000:
                violations.append(
                    f"High-value refund flagged for review: ${result['amount']}"
                )

    # Rule 3: Agent must never claim to directly process a refund
    forbidden_phrases = [
        "i will process your refund",
        "i am processing your refund",
        "refund has been processed",
        "i have processed",
    ]
    response_lower = response.lower()
    for phrase in forbidden_phrases:
        if phrase in response_lower:
            violations.append(f"Agent claimed to process refund directly: '{phrase}'")

    return {
        "passed": len(violations) == 0,
        "violations": violations,
    }
