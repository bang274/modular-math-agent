"""
Python Sandbox Executor — Tier 2 solver.

Person 2 owns this file.
Executes LLM-generated Python code in a sandboxed subprocess with safety restrictions.
"""

import asyncio
import re
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.tools.base import BaseTool, ToolResult
from app.telemetry.logger import logger


# Modules that are ALLOWED in the sandbox
ALLOWED_MODULES = {
    "math", "cmath", "numpy", "sympy", "scipy",
    "fractions", "decimal", "statistics", "itertools",
    "functools", "collections", "re", "json",
}

# Modules that are BLOCKED (dangerous)
BLOCKED_MODULES = {
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "requests", "httpx",
    "importlib", "ctypes", "signal", "threading",
    "multiprocessing", "pickle", "shelve",
    "builtins", "code", "compile", "eval", "exec",
}


class PythonExecutorTool(BaseTool):
    """Sandboxed Python code executor.

    Priority: TIER 2 — fallback after Wolfram Alpha fails.
    Safety: runs in subprocess with timeout and import restrictions.
    Retry: supports up to MAX_RETRIES attempts with error feedback.
    """

    name = "python_executor"
    description = (
        "Execute Python code in a sandboxed environment. "
        "Best for: numerical computation, algorithmic solutions. "
        "Allowed: math, numpy, sympy, scipy."
    )

    def __init__(self):
        self.settings = get_settings()

    async def execute(self, code: str, **kwargs) -> ToolResult:
        """Execute Python code in a sandboxed subprocess.

        Args:
            code: Python code string to execute.

        Returns:
            ToolResult with stdout output or error message.
        """
        # Step 1: Security validation
        security_check = self._validate_code(code)
        if security_check:
            return ToolResult(
                success=False,
                error=f"Security violation: {security_check}",
            )

        # Step 2: Execute in subprocess
        return await self._run_in_subprocess(code)

    def _validate_code(self, code: str) -> Optional[str]:
        """Check code for dangerous operations.

        Returns None if safe, or error message if dangerous.
        """
        if not code or not code.strip():
            return "Empty code"

        # Check for blocked module imports
        import_pattern = r'(?:import|from)\s+([\w.]+)'
        imports = re.findall(import_pattern, code)
        for module in imports:
            root_module = module.split(".")[0]
            if root_module in BLOCKED_MODULES:
                return f"Importing '{root_module}' is not allowed"
            if root_module not in ALLOWED_MODULES and root_module not in {"__future__"}:
                return f"Module '{root_module}' is not in the allowlist"

        # Check for dangerous built-in calls
        dangerous_patterns = [
            (r'\bopen\s*\(', "File operations (open) not allowed"),
            (r'\b__import__\s*\(', "__import__ not allowed"),
            (r'\bcompile\s*\(', "compile() not allowed"),
            (r'\bglobals\s*\(', "globals() not allowed"),
            (r'\blocals\s*\(', "locals() not allowed"),
            (r'\bgetattr\s*\(', "getattr() not allowed"),
            (r'\bsetattr\s*\(', "setattr() not allowed"),
            (r'\bdelattr\s*\(', "delattr() not allowed"),
        ]

        for pattern, msg in dangerous_patterns:
            if re.search(pattern, code):
                return msg

        return None

    async def _run_in_subprocess(self, code: str) -> ToolResult:
        """Run code in an isolated subprocess with timeout."""
        timeout = self.settings.python_sandbox_timeout_seconds

        # Write code to temporary file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                prefix="math_sandbox_",
            ) as f:
                f.write(code)
                tmp_path = f.name

            logger.info(f"[PythonExec] Running code ({len(code)} chars, timeout={timeout}s)")

            # Run in subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Limit resource usage
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Code execution timed out after {timeout}s "
                          f"(possible infinite loop)",
                )

            stdout_text = stdout.decode("utf-8", errors="replace").strip()
            stderr_text = stderr.decode("utf-8", errors="replace").strip()

            if process.returncode != 0:
                # Extract useful error info
                error_msg = self._extract_error(stderr_text)
                logger.warning(f"[PythonExec] Code error: {error_msg}")
                return ToolResult(
                    success=False,
                    output=stdout_text,
                    error=error_msg,
                    raw_data={"stderr": stderr_text, "returncode": process.returncode},
                )

            if not stdout_text:
                return ToolResult(
                    success=False,
                    error="Code produced no output. Make sure to print() the result.",
                )

            logger.info(f"[PythonExec] Output: {stdout_text[:200]}")
            return ToolResult(
                success=True,
                output=stdout_text,
                raw_data={"stderr": stderr_text} if stderr_text else {},
            )

        except Exception as e:
            logger.error(f"[PythonExec] Unexpected error: {e}")
            return ToolResult(success=False, error=str(e))

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _extract_error(self, stderr: str) -> str:
        """Extract the most useful error info from stderr."""
        if not stderr:
            return "Unknown error (no stderr)"

        lines = stderr.strip().split("\n")

        # Get last line (usually the actual error message)
        error_line = lines[-1] if lines else stderr

        # Also try to find traceback info
        for i, line in enumerate(lines):
            if "Error" in line or "Exception" in line:
                error_line = line
                break

        return error_line[:500]  # Limit length
