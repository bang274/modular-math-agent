"""
Base Tool Interface.

Person 2 owns this file.
All tools must implement this interface for consistent behavior.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time
from langsmith import traceable
from app.telemetry.logger import logger


@dataclass


class ToolResult:
    """Standardized result from any tool execution."""
    success: bool
    output: str = ""
    error: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    tool_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "tool_name": self.tool_name,
        }


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str = "base_tool"
    description: str = "Base tool"

    @abstractmethod
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute the tool with the given query.

        Args:
            query: The input query/expression for the tool.
            **kwargs: Additional tool-specific arguments.

        Returns:
            ToolResult with success status, output, and metadata.
        """
        ...

    async def safe_execute(self, query: str, **kwargs) -> ToolResult:
        """Execute with error handling and timing."""
        start = time.time()
        
        # Define a local traced function to allow dynamic naming
        @traceable(name=self.name, run_type="tool")
        async def _traced_execute():
            return await self.execute(query, **kwargs)

        try:
            result = await _traced_execute()
            result.latency_ms = int((time.time() - start) * 1000)
            result.tool_name = self.name
            return result
        except Exception as e:
            logger.error(f"[Tool] {self.name} failed: {e}")
            return ToolResult(
                success=False,
                error=f"{self.name} error: {str(e)}",
                latency_ms=int((time.time() - start) * 1000),
                tool_name=self.name,
            )


