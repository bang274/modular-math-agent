"""
Unit tests for math tools and agent parsing.
Runs offline — no API key needed.
"""

import os
import sys
import re
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.math_tools import (
    solve_equation,
    compute_derivative,
    compute_integral,
    evaluate_expression,
    TOOLS,
)


# ─── solve_equation ──────────────────────────────────────────────────────────

class TestSolveEquation:
    def test_linear(self):
        result = solve_equation("2*x + 3 = 7")
        assert "2" in result  # x = 2

    def test_quadratic(self):
        result = solve_equation("x**2 - 5*x + 6 = 0")
        assert "2" in result and "3" in result

    def test_no_equals(self):
        result = solve_equation("x**2 - 9")
        assert "3" in result  # x = ±3

    def test_no_solution(self):
        result = solve_equation("x**2 + 1 = 0")
        # Complex solutions — should still return something
        assert "x" in result.lower() or "solution" in result.lower() or "I" in result


# ─── compute_derivative ──────────────────────────────────────────────────────

class TestDerivative:
    def test_polynomial(self):
        result = compute_derivative("x**3 + 5*x**2 - 3*x + 7", "x")
        assert "3*x**2" in result
        assert "10*x" in result

    def test_trig(self):
        result = compute_derivative("sin(x)", "x")
        assert "cos(x)" in result

    def test_constant(self):
        result = compute_derivative("42", "x")
        assert "0" in result


# ─── compute_integral ────────────────────────────────────────────────────────

class TestIntegral:
    def test_polynomial(self):
        result = compute_integral("6*x**2 + 4*x - 1", "x")
        assert "2*x**3" in result
        assert "C" in result

    def test_simple(self):
        result = compute_integral("1", "x")
        assert "x" in result

    def test_trig(self):
        result = compute_integral("cos(x)", "x")
        assert "sin(x)" in result


# ─── evaluate_expression ─────────────────────────────────────────────────────

class TestEvaluate:
    def test_arithmetic(self):
        result = evaluate_expression("2 + 3 * 4")
        assert "14" in result

    def test_fraction(self):
        result = evaluate_expression("1/3 + 1/6")
        assert "1/2" in result or "0.5" in result

    def test_sqrt(self):
        result = evaluate_expression("sqrt(144)")
        assert "12" in result

    def test_complex_expression(self):
        result = evaluate_expression("(17 * 23) + (144 / 12) - sqrt(256)")
        assert "387" in result


# ─── Tool registry ───────────────────────────────────────────────────────────

class TestToolRegistry:
    def test_all_tools_have_keys(self):
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert callable(tool["function"])

    def test_tool_count(self):
        assert len(TOOLS) >= 4


# ─── Agent regex parsing ─────────────────────────────────────────────────────

class TestParsing:
    def test_action_parse(self):
        content = "Thought: I need to differentiate.\nAction: compute_derivative(x**3, x)"
        match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", content)
        assert match.group(1) == "compute_derivative"
        assert match.group(2) == "x**3, x"

    def test_final_answer_parse(self):
        content = "Thought: Done.\nFinal Answer: The derivative is 3x^2."
        match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL)
        assert "3x^2" in match.group(1)

    def test_multi_arg_split(self):
        raw = "x**2 + 1, x"
        args = [a.strip().strip("'\"") for a in raw.split(",")]
        assert args == ["x**2 + 1", "x"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
