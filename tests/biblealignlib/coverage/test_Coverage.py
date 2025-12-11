"""Test coverage dataclasses."""

import pytest

from biblealignlib.burrito import Source, Target
from biblealignlib.coverage import (
    BookCoverage,
    GroupCoverage,
    TokenCoverage,
    VerseCoverage,
)


class TestTokenCoverage:
    """Test TokenCoverage dataclass."""

    def test_init(self) -> None:
        """Test TokenCoverage initialization."""
        src = Source(id="41004003001", text="test", pos="noun")
        tc = TokenCoverage(token_id="41004003001", token=src, is_aligned=True)

        assert tc.token_id == "41004003001"
        assert tc.is_aligned is True
        assert tc.should_count is True

    def test_text_property(self) -> None:
        """Test text property."""
        src = Source(id="41004003001", text="test", pos="noun")
        tc = TokenCoverage(token_id="41004003001", token=src, is_aligned=True)

        assert tc.text == "test"

    def test_repr(self) -> None:
        """Test string representation."""
        src = Source(id="41004003001", text="test", pos="noun")
        tc = TokenCoverage(token_id="41004003001", token=src, is_aligned=True)

        assert "41004003001" in repr(tc)
        assert "aligned" in repr(tc)


class TestVerseCoverage:
    """Test VerseCoverage dataclass."""

    def test_init_with_zero_total(self) -> None:
        """Test VerseCoverage with zero tokens."""
        vc = VerseCoverage(
            bcvid="41004003",
            source_total=0,
            source_aligned=0,
            source_unaligned=0,
            target_total=0,
            target_aligned=0,
            target_unaligned=0,
        )

        assert vc.source_coverage_pct == 0.0
        assert vc.target_coverage_pct == 0.0

    def test_percentage_computation(self) -> None:
        """Test percentage computation in __post_init__."""
        vc = VerseCoverage(
            bcvid="41004003",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=20,
            target_aligned=15,
            target_unaligned=5,
        )

        assert vc.source_coverage_pct == 80.0
        assert vc.target_coverage_pct == 75.0

    def test_summary_brief(self) -> None:
        """Test brief summary format."""
        vc = VerseCoverage(
            bcvid="41004003",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=20,
            target_aligned=15,
            target_unaligned=5,
        )

        summary = vc.summary(brief=True)
        assert "41004003" in summary
        assert "8/10" in summary
        assert "15/20" in summary

    def test_asdict(self) -> None:
        """Test asdict method."""
        vc = VerseCoverage(
            bcvid="41004003",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=20,
            target_aligned=15,
            target_unaligned=5,
        )

        d = vc.asdict()
        assert d["BCVID"] == "41004003"
        assert d["Source_Total"] == 10
        assert d["Source_Aligned"] == 8
        assert d["Target_Coverage_Pct"] == 75.0


class TestBookCoverage:
    """Test BookCoverage dataclass."""

    def test_aggregation(self) -> None:
        """Test aggregation from verse coverages."""
        vc1 = VerseCoverage(
            bcvid="41001001",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=15,
            target_aligned=12,
            target_unaligned=3,
        )
        vc2 = VerseCoverage(
            bcvid="41001002",
            source_total=5,
            source_aligned=4,
            source_unaligned=1,
            target_total=8,
            target_aligned=6,
            target_unaligned=2,
        )

        bc = BookCoverage(book_id="41", verse_coverages=[vc1, vc2])

        assert bc.source_total == 15  # 10 + 5
        assert bc.source_aligned == 12  # 8 + 4
        assert bc.target_total == 23  # 15 + 8
        assert bc.target_aligned == 18  # 12 + 6

    def test_summary(self) -> None:
        """Test summary format."""
        vc = VerseCoverage(
            bcvid="41001001",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=15,
            target_aligned=12,
            target_unaligned=3,
        )

        bc = BookCoverage(book_id="41", verse_coverages=[vc])
        summary = bc.summary()

        assert "Book 41" in summary
        assert "8/10" in summary


class TestGroupCoverage:
    """Test GroupCoverage dataclass."""

    def test_aggregation(self) -> None:
        """Test aggregation from verse coverages."""
        vc1 = VerseCoverage(
            bcvid="41001001",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=15,
            target_aligned=12,
            target_unaligned=3,
        )
        vc2 = VerseCoverage(
            bcvid="42001001",
            source_total=5,
            source_aligned=4,
            source_unaligned=1,
            target_total=8,
            target_aligned=6,
            target_unaligned=2,
        )

        gc = GroupCoverage(identifier="all", verse_coverages=[vc1, vc2])

        assert gc.source_total == 15
        assert gc.source_aligned == 12
        assert gc.target_total == 23
        assert gc.target_aligned == 18

    def test_summary_dict(self) -> None:
        """Test summary_dict format."""
        vc = VerseCoverage(
            bcvid="41001001",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=15,
            target_aligned=12,
            target_unaligned=3,
        )

        gc = GroupCoverage(identifier="test", verse_coverages=[vc])
        sd = gc.summary_dict()

        assert "Source_Coverage" in sd
        assert "Target_Coverage" in sd
        assert "%" in sd["Source_Coverage"]
