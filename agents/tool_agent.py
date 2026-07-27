import os
from agents.response_agent import get_response
from tools.calculator import calculate, extract_math_from_query
from tools.python_tool import execute_code, extract_python_from_query
from tools.pdf_tool import extract_pdf_text, search_pdf


TOOL_SYSTEM_PROMPT = (
    "You are a tool-calling agent that determines which tool to use based on user queries. "
    "Available tools:\n"
    "1. CALCULATOR - For math calculations (e.g., 'What is 25 * 4?')\n"
    "2. PYTHON - For code execution or data processing\n"
    "3. PDF - For PDF-specific operations (e.g., 'Summarize page 3 of the PDF')\n"
    "4. WEB_SEARCH - For real-time information\n"
    "5. RAG - For document-based questions\n\n"
    "Analyze the query and determine the best tool to use."
)


def classify_tool(question: str):

    q = question.lower()

    math_keywords = [
        "calculate", "math", "sum", "add", "subtract", "multiply",
        "divide", "equation", "formula", "what is", "how many",
        "percentage", "ratio", "average", "total"
    ]

    code_keywords = [
        "code", "program", "script", "python", "function",
        "execute", "run code", "debug", "algorithm"
    ]

    pdf_keywords = [
        "pdf", "document", "page", "extract", "summarize page",
        "table", "figure", "image from pdf"
    ]

    if any(word in q for word in math_keywords):
        return "CALCULATOR"

    if any(word in q for word in code_keywords):
        return "PYTHON"

    if any(word in q for word in pdf_keywords):
        return "PDF"

    return "RAG"


def use_calculator(question: str) -> str:

    math_expr = extract_math_from_query(question)
    return calculate(math_expr)


def use_python(question: str) -> str:

    code = extract_python_from_query(question)
    result = execute_code(code)

    if result["success"]:
        return result["output"] if result["output"] else "Code executed successfully (no output)"
    else:
        return f"Error: {result['error']}"


def use_pdf(question: str) -> str:

    import glob
    pdf_files = glob.glob("./uploads/*.pdf")

    if not pdf_files:
        return "No PDF files found in uploads directory."

    latest_pdf = max(pdf_files, key=os.path.getmtime) if pdf_files else None

    if not latest_pdf:
        return "No PDF files available."

    import re
    page_match = re.search(r'page\s+(\d+)', question.lower())
    if page_match:
        page_num = int(page_match.group(1))
        return extract_pdf_text(latest_pdf, str(page_num))

    return extract_pdf_text(latest_pdf)


def tool_response(question: str, tool_name: str, tool_result: str):

    prompt = (
        f"Tool Used: {tool_name}\n"
        f"Tool Result: {tool_result}\n\n"
        f"Original Question: {question}\n\n"
        f"Format the tool result into a clear, helpful response:"
    )

    return get_response(prompt)


def process_with_tool(question: str, tools: dict = None):

    tool_name = classify_tool(question)

    tool_functions = {
        "CALCULATOR": use_calculator,
        "PYTHON": use_python,
        "PDF": use_pdf,
    }

    if tool_name in tool_functions:
        try:
            result = tool_functions[tool_name](question)
            return tool_response(question, tool_name, result), tool_name
        except Exception as e:
            print(f"Tool {tool_name} failed: {e}")

    return None, tool_name
