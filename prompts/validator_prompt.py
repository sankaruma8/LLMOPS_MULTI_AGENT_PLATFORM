VALIDATOR_SYSTEM_PROMPT = """You are an answer quality validator. Your job is to evaluate whether an answer is satisfactory.

An answer is VALID if it:
- Directly addresses the user's question
- Contains specific information (not generic)
- Is at least 2-3 sentences long
- Does not contain failure phrases

An answer is INVALID if it:
- Contains phrases like "I couldn't find", "I don't know", "sorry"
- Is too short or vague
- Doesn't actually answer the question
- Says "not available" or "no information"
"""

VALIDATOR_CHECK_PROMPT = """Evaluate if this answer adequately responds to the question.

Question: {question}

Answer: {answer}

Return ONLY "VALID" or "INVALID" with a brief reason."""

FAILURE_PHRASES = [
    "i couldn't find",
    "i could not find",
    "no relevant",
    "not available",
    "don't know",
    "unable to answer",
    "no information",
    "sorry",
    "i don't have",
    "i do not have",
    "cannot determine",
    "unable to determine",
    "no data",
    "not found",
]


def validate_answer(answer: str) -> bool:
    if not answer or len(answer.strip()) < 10:
        return False

    answer_lower = answer.lower()

    for phrase in FAILURE_PHRASES:
        if phrase in answer_lower:
            return False

    return True
