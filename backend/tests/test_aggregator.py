"""Tests for aggregator node behavior and follow-up fallbacks."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.nodes.aggregator import aggregator_node


class TestAggregatorFollowUp:
    @pytest.mark.asyncio
    async def test_followup_fallback_when_llm_fails(self):
        state = {
            "problems": [],
            "raw_text": "giai bai nay",
            "extraction_error": "upstream model unavailable",
            "ws_messages": [],
        }

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = RuntimeError("llm down")

        with patch("app.agent.nodes.aggregator.get_aggregator_llm", return_value=mock_llm):
            result = await aggregator_node(state)

        assert result["status"] == "failed"
        assert len(result["final_results"]) == 1
        assert "upstream model unavailable" in result["final_results"][0]["final_answer"]
        assert result["ws_messages"][-1]["type"] == "all_complete"

    @pytest.mark.asyncio
    async def test_followup_success_when_llm_returns_valid_json(self):
        state = {
            "problems": [],
            "raw_text": "tai sao bai nay ra ket qua do",
            "ws_messages": [],
            "chat_history": [{"role": "user", "content": "x+1=2"}],
        }

        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = SimpleNamespace(
            content='{"steps":[{"step":1,"description":"Giai thich","latex":"x=1"}],"final_answer":"x=1"}'
        )

        with patch("app.agent.nodes.aggregator.get_aggregator_llm", return_value=mock_llm):
            result = await aggregator_node(state)

        assert result["status"] == "completed"
        assert len(result["final_results"]) == 1
        assert result["final_results"][0]["tool_trace"]["route"] == "clarification"
        assert result["final_results"][0]["final_answer"] == "x=1"


class TestAggregatorCachePath:
    @pytest.mark.asyncio
    async def test_cached_problem_skips_llm_aggregation(self):
        state = {
            "problems": [{"id": 1, "content": "x+1=2", "difficulty": "easy"}],
            "results": {},
            "cache_hits": {1: {"steps": [{"step": 1, "description": "cache", "latex": "x=1"}], "final_answer": "x=1", "confidence": 1.0}},
            "ws_messages": [],
        }

        mock_llm = AsyncMock()

        with patch("app.agent.nodes.aggregator.get_aggregator_llm", return_value=mock_llm):
            result = await aggregator_node(state)

        assert result["status"] == "completed"
        assert result["cached_count"] == 1
        assert len(result["final_results"]) == 1
        assert result["final_results"][0]["tool_trace"]["cache_hit"] is True
        assert mock_llm.ainvoke.await_count == 0
