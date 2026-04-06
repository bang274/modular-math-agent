"""
Tests for cache module.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.cache.prompt_cache import PromptCache


class TestPromptCache:
    @pytest.fixture
    def cache(self):
        return PromptCache()

    def test_normalize_strips_whitespace(self, cache):
        result = cache._normalize("  x + 1  ")
        assert result == "x + 1"

    def test_normalize_collapses_spaces(self, cache):
        result = cache._normalize("x  +  1")
        assert result == "x + 1"

    def test_normalize_latex_braces(self, cache):
        result = cache._normalize("\\frac { 1 } { 2 }")
        assert result == "\\frac{1}{2}"

    def test_make_key_consistent(self, cache):
        """Same content should produce same key."""
        key1 = cache._make_key("x^2 + 1")
        key2 = cache._make_key("x^2 + 1")
        assert key1 == key2

    def test_make_key_different_content(self, cache):
        """Different content should produce different keys."""
        key1 = cache._make_key("x^2 + 1")
        key2 = cache._make_key("x^3 + 1")
        assert key1 != key2

    def test_make_key_normalized(self, cache):
        """Equivalent content with different spacing should match."""
        key1 = cache._make_key("x + 1")
        key2 = cache._make_key("  x  +  1  ")
        assert key1 == key2
