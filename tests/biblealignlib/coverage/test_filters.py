"""Test coverage filter functions."""

import pytest

from biblealignlib.burrito import Source, Target
from biblealignlib.coverage import CoverageFilter
from biblealignlib.coverage.filters import get_source_filter, get_target_filter


class TestCoverageFilter:
    """Test CoverageFilter enum."""

    def test_enum_values(self) -> None:
        """Test enum has expected values."""
        assert CoverageFilter.ALL.value == "all"
        assert CoverageFilter.CONTENT.value == "content"
        assert CoverageFilter.NONEXCLUDED.value == "nonexcluded"
        assert CoverageFilter.CONTENT_NONEXCLUDED.value == "content_nonexcluded"

    def test_description(self) -> None:
        """Test description property."""
        assert "all tokens" in CoverageFilter.ALL.description.lower()
        assert "content" in CoverageFilter.CONTENT.description.lower()


class TestSourceFilter:
    """Test source filter functions."""

    def test_all_filter(self) -> None:
        """Test ALL filter accepts all sources."""
        filter_fn = get_source_filter(CoverageFilter.ALL)
        # Create dummy source tokens
        content_src = Source(id="41004003001", pos="noun", text="test")
        function_src = Source(id="41004003002", pos="prep", text="of")

        assert filter_fn(content_src) is True
        assert filter_fn(function_src) is True

    def test_content_filter(self) -> None:
        """Test CONTENT filter only accepts content words."""
        filter_fn = get_source_filter(CoverageFilter.CONTENT)

        content_src = Source(id="41004003001", pos="noun", text="test")
        function_src = Source(id="41004003002", pos="prep", text="of")

        assert filter_fn(content_src) is True
        assert filter_fn(function_src) is False

    def test_nonexcluded_filter(self) -> None:
        """Test NONEXCLUDED filter accepts all sources."""
        filter_fn = get_source_filter(CoverageFilter.NONEXCLUDED)

        content_src = Source(id="41004003001", pos="noun", text="test")
        function_src = Source(id="41004003002", pos="prep", text="of")

        # NONEXCLUDED doesn't filter sources
        assert filter_fn(content_src) is True
        assert filter_fn(function_src) is True


class TestTargetFilter:
    """Test target filter functions."""

    def test_all_filter(self) -> None:
        """Test ALL filter accepts all targets."""
        filter_fn = get_target_filter(CoverageFilter.ALL)

        normal_trg = Target(id="41004003001", text="test", exclude=False)
        excluded_trg = Target(id="41004003002", text="the", exclude=True)

        assert filter_fn(normal_trg) is True
        assert filter_fn(excluded_trg) is True

    def test_content_filter(self) -> None:
        """Test CONTENT filter only accepts non-excluded targets."""
        filter_fn = get_target_filter(CoverageFilter.CONTENT)

        normal_trg = Target(id="41004003001", text="test", exclude=False)
        excluded_trg = Target(id="41004003002", text="the", exclude=True)

        assert filter_fn(normal_trg) is True
        assert filter_fn(excluded_trg) is False

    def test_nonexcluded_filter(self) -> None:
        """Test NONEXCLUDED filter only accepts non-excluded targets."""
        filter_fn = get_target_filter(CoverageFilter.NONEXCLUDED)

        normal_trg = Target(id="41004003001", text="test", exclude=False)
        excluded_trg = Target(id="41004003002", text="the", exclude=True)

        assert filter_fn(normal_trg) is True
        assert filter_fn(excluded_trg) is False
