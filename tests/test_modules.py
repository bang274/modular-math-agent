"""
Tests for the tiered fallback logic and new tool modules.
Runs OFFLINE — no API keys needed.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.python_tool import run_python_code, PYTHON_TOOL
from src.tools.wolfram_tool import WOLFRAM_TOOL
from src.tools.search_tool import SEARCH_TOOL
from src.input.ocr_engine import parse_question, _clean_math_text


# ─── Python Tool Tests ───────────────────────────────────────────────────────

class TestPythonTool:
    def test_basic_execution(self):
        result = run_python_code("print(2 + 3)")
        assert "5" in result

    def test_sympy_available(self):
        code = "import sympy as sp; x = sp.Symbol('x'); print(sp.diff(x**3, x))"
        result = run_python_code(code)
        assert "3*x**2" in result

    def test_math_available(self):
        code = "import math; print(math.sqrt(144))"
        result = run_python_code(code)
        assert "12" in result

    def test_error_returns_message(self):
        result = run_python_code("print(1/0)")
        assert "ZeroDivisionError" in result

    def test_no_output_warning(self):
        result = run_python_code("x = 42")
        assert "no output" in result.lower()

    def test_blocks_os_import(self):
        result = run_python_code("import os; print(os.getcwd())")
        assert "BLOCKED" in result

    def test_blocks_subprocess(self):
        result = run_python_code("import subprocess; subprocess.run(['ls'])")
        assert "BLOCKED" in result

    def test_tool_registration(self):
        assert PYTHON_TOOL["name"] == "run_python"
        assert callable(PYTHON_TOOL["function"])


# ─── Wolfram Tool Tests (no API key needed) ──────────────────────────────────

class TestWolframTool:
    def test_tool_registration(self):
        assert WOLFRAM_TOOL["name"] == "wolfram_alpha"
        assert callable(WOLFRAM_TOOL["function"])

    def test_no_api_key_error(self):
        # Without a real key, should return an error message
        old = os.environ.get("WOLFRAM_APP_ID", "")
        os.environ["WOLFRAM_APP_ID"] = ""
        result = WOLFRAM_TOOL["function"]("2 + 2")
        assert "error" in result.lower() or "not set" in result.lower()
        if old:
            os.environ["WOLFRAM_APP_ID"] = old


# ─── Search Tool Tests (no API key needed) ────────────────────────────────────

class TestSearchTool:
    def test_tool_registration(self):
        assert SEARCH_TOOL["name"] == "search_web"
        assert callable(SEARCH_TOOL["function"])

    def test_no_api_key_error(self):
        old = os.environ.get("TAVILY_API_KEY", "")
        os.environ["TAVILY_API_KEY"] = ""
        result = SEARCH_TOOL["function"]("derivative of x^3")
        assert "error" in result.lower() or "not set" in result.lower() or "not installed" in result.lower()
        if old:
            os.environ["TAVILY_API_KEY"] = old


# ─── OCR Parser Tests ────────────────────────────────────────────────────────

class TestOCRParser:
    def test_parse_single_line(self):
        result = parse_question("Find the derivative of x^3 + 2x")
        assert result["question"] == "Find the derivative of x^3 + 2x"
        assert result["source"] == "ocr"

    def test_parse_multi_line(self):
        result = parse_question("Solve for x\n2x + 3 = 7")
        assert result["question"] == "Solve for x"
        assert "2x + 3 = 7" in result["details"]

    def test_parse_empty(self):
        result = parse_question("")
        assert result.get("error")

    def test_clean_math_text(self):
        result = _clean_math_text("x² + 3x − 5 = 0")
        assert "**2" in result
        assert "-" in result


# ─── Tool Registry Completeness ──────────────────────────────────────────────

class TestToolRegistry:
    def test_all_three_main_tools_exist(self):
        tool_names = [WOLFRAM_TOOL["name"], PYTHON_TOOL["name"], SEARCH_TOOL["name"]]
        assert "wolfram_alpha" in tool_names
        assert "run_python" in tool_names
        assert "search_web" in tool_names

    def test_all_have_required_keys(self):
        for tool in [WOLFRAM_TOOL, PYTHON_TOOL, SEARCH_TOOL]:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert callable(tool["function"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
