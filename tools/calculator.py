import re
import numexpr


SAFE_NUMPY_FUNCTIONS = [
    "abs", "array", "ceil", "floor", "round", "sqrt",
    "log", "log10", "log2", "exp", "power",
    "sin", "cos", "tan", "arcsin", "arccos", "arctan",
    "min", "max", "sum", "mean", "std", "median",
    "pi", "e", "inf", "nan"
]

BLOCKED_PATTERNS = [
    r"import\s",
    r"from\s",
    r"open\s*\(",
    r"exec\s*\(",
    r"eval\s*\(",
    r"__\w+__",
    r"(?<!\d)\.(?!\d)",
    r"(?<!\d)\[(?!\d)",
]


def clean_expression(expr: str) -> str:

    expr = expr.strip()

    expr = re.sub(r'[^\d\w\s\+\-\*\/\%\.\,\(\)\[\]\{\}\=\>\<\!\~\^]', '', expr)

    expr = expr.replace("x", "*")
    expr = expr.replace("X", "*")
    expr = expr.replace("^", "**")

    expr = expr.replace("pi", "numpy.pi")
    expr = expr.replace("e", "numpy.e")

    return expr


def is_safe_expression(expr: str) -> bool:

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, expr):
            return False

    return True


def calculate(expression: str) -> str:

    try:
        cleaned = clean_expression(expression)

        if not is_safe_expression(cleaned):
            return "Error: Expression contains unsafe operations"

        import numpy

        local_dict = {"numpy": numpy}

        for func_name in SAFE_NUMPY_FUNCTIONS:
            if hasattr(numpy, func_name):
                local_dict[func_name] = getattr(numpy, func_name)

        result = numexpr.evaluate(cleaned, local_dict=local_dict)

        return f"Result: {result}"

    except ZeroDivisionError:
        return "Error: Division by zero"

    except Exception as e:
        return f"Error calculating expression: {str(e)}"


def extract_math_from_query(query: str) -> str:

    q = query.lower().strip()

    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*of\s+(\d+(?:\.\d+)?)', q)
    if pct_match:
        return f"{pct_match.group(1)} / 100 * {pct_match.group(2)}"

    math_patterns = [
        r"calculate\s+(.+)",
        r"what\s+is\s+(.+)",
        r"compute\s+(.+)",
        r"solve\s+(.+)",
        r"(\d+[\s\+\-\*\/\^\(\)]+\d+)",
    ]

    for pattern in math_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return query
