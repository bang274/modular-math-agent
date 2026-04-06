"""
Math tools powered by sympy for the ReAct Agent.
Covers: algebra (equation solving), calculus (derivatives, integrals), and arithmetic.

=== TEAM: Edit the TOOLS list descriptions and test edge cases ===
"""

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


# ─── Parsing helper ──────────────────────────────────────────────────────────

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


def _safe_parse(expr_str: str) -> sp.Expr:
    """Parse a math expression string into a sympy expression."""
    cleaned = expr_str.strip().replace("^", "**")
    return parse_expr(cleaned, transformations=TRANSFORMS)


# ─── Tool functions ──────────────────────────────────────────────────────────

def solve_equation(equation: str) -> str:
    """
    Solve an algebraic equation for x.
    Input should be an equation with '=' sign, e.g. '2*x + 3 = 7' or 'x**2 - 4 = 0'.
    If no '=' sign, assumes the expression equals 0.
    """
    try:
        x = sp.Symbol("x")
        if "=" in equation:
            left, right = equation.split("=", 1)
            expr = _safe_parse(left) - _safe_parse(right)
        else:
            expr = _safe_parse(equation)

        solutions = sp.solve(expr, x)

        if not solutions:
            return f"No solution found for: {equation}"

        sol_str = ", ".join(str(s) for s in solutions)
        return f"Solutions for [{equation}]: x = {sol_str}"

    except Exception as e:
        return f"Error solving equation '{equation}': {e}"


def compute_derivative(expression: str, variable: str = "x") -> str:
    """
    Compute the symbolic derivative of an expression with respect to a variable.
    Example: compute_derivative('x**3 + 2*x', 'x') → '3*x**2 + 2'
    """
    try:
        var = sp.Symbol(variable.strip())
        expr = _safe_parse(expression)
        result = sp.diff(expr, var)
        return f"d/d{variable}[{expression}] = {result}"

    except Exception as e:
        return f"Error computing derivative of '{expression}': {e}"


def compute_integral(expression: str, variable: str = "x") -> str:
    """
    Compute the symbolic indefinite integral of an expression.
    Example: compute_integral('3*x**2 + 2', 'x') → 'x**3 + 2*x + C'
    """
    try:
        var = sp.Symbol(variable.strip())
        expr = _safe_parse(expression)
        result = sp.integrate(expr, var)
        return f"∫({expression}) d{variable} = {result} + C"

    except Exception as e:
        return f"Error computing integral of '{expression}': {e}"


def evaluate_expression(expression: str) -> str:
    """
    Evaluate a numerical math expression and return the exact result.
    Handles fractions, square roots, powers, etc.
    Example: evaluate('(3/7) * 49 + sqrt(16)') → '25'
    """
    try:
        expr = _safe_parse(expression)
        result = sp.simplify(expr)

        # Try to produce a numeric value if fully numeric
        numeric = result.evalf()
        if result.is_number:
            # Show exact form if it's a nice fraction, else decimal
            if result.is_Rational and result.q != 1:
                return f"{expression} = {result} (≈ {float(numeric):.6f})"
            return f"{expression} = {numeric}"

        return f"{expression} = {result}"

    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


# ─── Tool Registry ───────────────────────────────────────────────────────────
# === TEAM: Edit these descriptions to be more precise for your use case ===

TOOLS = [
    {
        "name": "solve_equation",
        "description": (
            "Solve an algebraic equation for x. "
            "Input: a single equation string. Use '=' for equations (e.g. '2*x + 3 = 7'). "
            "If no '=' is given, solves expression = 0. "
            "Supports quadratic, linear, and polynomial equations."
        ),
        "function": solve_equation,
    },
    {
        "name": "compute_derivative",
        "description": (
            "Compute the symbolic derivative of a math expression. "
            "Input: expression (string), variable (string, default 'x'). "
            "Format: compute_derivative(expression, variable). "
            "Example: compute_derivative(x**3 + 2*x, x) returns 3*x**2 + 2."
        ),
        "function": compute_derivative,
    },
    {
        "name": "compute_integral",
        "description": (
            "Compute the symbolic indefinite integral of a math expression. "
            "Input: expression (string), variable (string, default 'x'). "
            "Format: compute_integral(expression, variable). "
            "Example: compute_integral(3*x**2 + 2, x) returns x**3 + 2*x + C."
        ),
        "function": compute_integral,
    },
    {
        "name": "evaluate",
        "description": (
            "Evaluate a numerical math expression to get an exact answer. "
            "Supports +, -, *, /, **, sqrt(), fractions, and parentheses. "
            "Input: expression (string). "
            "Example: evaluate((3/7) * 49 + sqrt(16)) returns 25."
        ),
        "function": evaluate_expression,
    },
]
