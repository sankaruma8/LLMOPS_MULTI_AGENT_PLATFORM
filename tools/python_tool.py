import subprocess
import sys
import tempfile
import os
import signal
from typing import Optional


class CodeExecutor:

    def __init__(self, timeout: int = 30, max_output_size: int = 10000):
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.blocked_modules = [
            "os", "sys", "subprocess", "shutil",
            "pathlib", "socket", "http", "urllib",
            "requests", "ctypes", "importlib"
        ]

    def validate_code(self, code: str) -> tuple[bool, str]:

        code_lower = code.lower()

        for module in self.blocked_modules:
            if f"import {module}" in code_lower or f"from {module}" in code_lower:
                return False, f"Module '{module}' is not allowed"

        dangerous_patterns = [
            "exec(", "eval(", "__import__(",
            "compile(", "globals(", "locals(",
            "open(", "file(", "input(",
            "breakpoint(", "exit(", "quit("
        ]

        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return False, f"Dangerous pattern '{pattern}' is not allowed"

        return True, "Code is safe"

    def execute(self, code: str, language: str = "python") -> dict:

        is_safe, message = self.validate_code(code)
        if not is_safe:
            return {
                "success": False,
                "output": "",
                "error": f"Security check failed: {message}",
                "language": language
            }

        if language == "python":
            return self._execute_python(code)
        else:
            return {
                "success": False,
                "output": "",
                "error": f"Language '{language}' is not supported",
                "language": language
            }

    def _execute_python(self, code: str) -> dict:

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONUNBUFFERED": "1"
                }
            )

            output = result.stdout[:self.max_output_size]
            error = result.stderr[:self.max_output_size]

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": output,
                    "error": "",
                    "language": "python"
                }
            else:
                return {
                    "success": False,
                    "output": output,
                    "error": error,
                    "language": "python"
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Code execution timed out after {self.timeout} seconds",
                "language": "python"
            }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "language": "python"
            }

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


executor = CodeExecutor()


def execute_code(code: str, language: str = "python") -> dict:
    return executor.execute(code, language)


def run_python_script(script: str) -> str:

    result = execute_code(script, "python")

    if result["success"]:
        return result["output"] if result["output"] else "Script executed successfully (no output)"
    else:
        return f"Error: {result['error']}"


def extract_python_from_query(query: str) -> str:

    import re

    code_block_match = re.search(r'```python\s*(.*?)\s*```', query, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)

    code_block_match = re.search(r'```\s*(.*?)\s*```', query, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)

    lines = query.split('\n')
    code_lines = []
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(kw) for kw in [
            'def ', 'class ', 'import ', 'from ',
            'if ', 'for ', 'while ', 'print(',
            'return ', 'yield ', 'try:', 'except',
            'with ', 'as ', 'lambda '
        ]):
            code_lines.append(line)
        elif '=' in stripped and not stripped.startswith('#'):
            code_lines.append(line)

    if code_lines:
        return '\n'.join(code_lines)

    return f"print({query})"
