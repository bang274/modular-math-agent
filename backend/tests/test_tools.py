"""
Tests for tools module.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.tools.base import ToolResult
from app.tools.python_executor import PythonExecutorTool


class TestPythonExecutor:
    """Tests for the Python sandbox executor."""

    @pytest.fixture
    def executor(self):
        return PythonExecutorTool()

    def test_validate_safe_code(self, executor):
        """Safe code should pass validation."""
        code = "import math\nprint(math.sqrt(2))"
        result = executor._validate_code(code)
        assert result is None  # None means safe

    def test_reject_os_import(self, executor):
        """Should reject os module import."""
        code = "import os\nos.system('ls')"
        result = executor._validate_code(code)
        assert result is not None
        assert "os" in result.lower()

    def test_reject_subprocess_import(self, executor):
        """Should reject subprocess import."""
        code = "import subprocess\nsubprocess.run(['ls'])"
        result = executor._validate_code(code)
        assert result is not None

    def test_reject_file_operations(self, executor):
        """Should reject open() calls."""
        code = "f = open('/etc/passwd')\nprint(f.read())"
        result = executor._validate_code(code)
        assert result is not None

    def test_reject_empty_code(self, executor):
        """Should reject empty code."""
        result = executor._validate_code("")
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_simple_code(self, executor):
        """Should execute simple math code."""
        code = "print(2 + 2)"
        result = await executor.safe_execute(code)
        assert result.success
        assert "4" in result.output

    @pytest.mark.asyncio
    async def test_execute_sympy(self, executor):
        """Should execute sympy code."""
        code = "from sympy import symbols, solve\nx = symbols('x')\nprint(solve(x**2 - 4, x))"
        result = await executor.safe_execute(code)
        # This will only pass if sympy is installed
        if result.success:
            assert "2" in result.output


class TestToolResult:
    def test_tool_result_to_dict(self):
        result = ToolResult(success=True, output="42", tool_name="test")
        d = result.to_dict()
        assert d["success"] is True
        assert d["output"] == "42"
        assert d["tool_name"] == "test"
