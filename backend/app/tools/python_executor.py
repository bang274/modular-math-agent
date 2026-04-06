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
from app.telemetry.logger import logger
from dataclasses import field

@dataclass
class ToolResult:
    """Standardized result from any tool execution."""
    success: bool
    output: str = ""
    error: Optional[str] = None
    latency_ms: int = 0
    tool_name: str = ""
    images: List[str] = field(default_factory=list)  # Base64 encoded images
    raw_data: Dict[str, Any] = field(default_factory=dict)



# Modules that are ALLOWED in the sandbox
ALLOWED_MODULES = {
    "math", "cmath", "numpy", "sympy", "scipy", "matplotlib", "pyplot", "pandas",
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

    name = "python_codegen"

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

        # Auto-inject Agg backend for matplotlib if used
        if "matplotlib" in code or "plt." in code:
            code = "import matplotlib\nmatplotlib.use('Agg')\n" + code

        # Use a temporary directory to capture generated plots
        with tempfile.TemporaryDirectory(prefix="math_plot_") as plot_dir:
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".py",
                    delete=False,
                    dir=plot_dir,
                ) as f:
                    f.write(code)
                    tmp_path = f.name

                process = await asyncio.create_subprocess_exec(
                    sys.executable, tmp_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=plot_dir,  # Run in the plot dir to capture outputs
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    return ToolResult(success=False, error=f"Timeout after {timeout}s")

                stdout_text = stdout.decode("utf-8", errors="replace").strip()
                stderr_text = stderr.decode("utf-8", errors="replace").strip()

                # Capture any PNG files created in the directory
                images = []
                for file_name in os.listdir(plot_dir):
                    if file_name.endswith(".png"):
                        full_path = os.path.join(plot_dir, file_name)
                        with open(full_path, "rb") as image_file:
                            encoded = base64.b64encode(image_file.read()).decode("utf-8")
                            images.append(encoded)

                if process.returncode != 0:
                    error_msg = self._extract_error(stderr_text)
                    return ToolResult(success=False, output=stdout_text, error=error_msg, images=images)

                if not stdout_text and not images:
                    return ToolResult(success=False, error="No output or plot produced.")

                return ToolResult(success=True, output=stdout_text, images=images)

            finally:
                if 'tmp_path' in locals():
                    try: os.unlink(tmp_path)
                    except: pass


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
