try:
    from tools.calculator import calculate, extract_math_from_query
except ImportError:
    calculate = extract_math_from_query = None

try:
    from tools.web_search import web_search, get_cached_queries, clear_search_cache
except ImportError:
    web_search = get_cached_queries = clear_search_cache = None

try:
    from tools.python_tool import execute_code, run_python_script
except ImportError:
    execute_code = run_python_script = None

try:
    from tools.pdf_tool import extract_pdf_text, search_pdf, get_pdf_info, extract_pdf_tables
except ImportError:
    extract_pdf_text = search_pdf = get_pdf_info = extract_pdf_tables = None
