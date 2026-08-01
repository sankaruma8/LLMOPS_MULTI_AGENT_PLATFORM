from prompts.validator_prompt import FAILURE_PHRASES


def validate_answer_standalone(answer: str) -> bool:

    if not answer or len(answer.strip()) < 10:
        return False

    answer_lower = answer.lower()

    for phrase in FAILURE_PHRASES:
        if phrase in answer_lower:
            return False

    return True
