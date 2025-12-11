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

        bc = BookCoverage(
            book_id="41",
            verse_coverages=[vc1, vc2],
            source_token_count=20,
            verse_count=2,
        )

        assert bc.source_total == 15  # 10 + 5
        assert bc.source_aligned == 12  # 8 + 4
        assert bc.target_total == 23  # 15 + 8
        assert bc.target_aligned == 18  # 12 + 6

    def test_new_metrics(self) -> None:
        """Test new book-level metrics (verse coverage and token alignment)."""
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

        # Book has 20 total tokens and 5 total verses
        bc = BookCoverage(
            book_id="41",
            verse_coverages=[vc1, vc2],
            source_token_count=20,
            verse_count=5,
        )

        # Verify verse coverage
        assert bc.verses_with_alignments == 2  # 2 verses have alignment data
        assert bc.verse_count == 5  # Total verses in book
        assert bc.verse_coverage_pct == 40.0  # 2/5 = 40%

        # Verify token alignment percentage
        assert bc.source_aligned == 12  # 8 + 4 tokens aligned
        assert bc.source_token_count == 20  # Total tokens in entire book
        assert bc.source_token_aligned_pct == 60.0  # 12/20 = 60%

    def test_new_metrics_edge_cases(self) -> None:
        """Test edge cases for new metrics."""
        vc = VerseCoverage(
            bcvid="41001001",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=15,
            target_aligned=12,
            target_unaligned=3,
        )

        # Case 1: All verses have alignments (100% verse coverage)
        bc1 = BookCoverage(
            book_id="41",
            verse_coverages=[vc],
            source_token_count=15,
            verse_count=1,
        )
        assert bc1.verse_coverage_pct == 100.0  # 1/1 = 100%
        assert bc1.source_token_aligned_pct == pytest.approx(53.33, rel=0.01)  # 8/15

        # Case 2: Multiple verses, not all have alignments
        bc2 = BookCoverage(
            book_id="41",
            verse_coverages=[vc],
            source_token_count=20,
            verse_count=5,
        )
        assert bc2.verse_coverage_pct == 20.0  # 1/5 = 20%
        assert bc2.source_token_aligned_pct == 40.0  # 8/20 = 40%

        # Case 3: Book has more tokens than just the aligned verses
        bc3 = BookCoverage(
            book_id="41",
            verse_coverages=[vc],
            source_token_count=50,  # Book has 50 total tokens
            verse_count=10,  # Book has 10 verses total
        )
        assert bc3.verse_coverage_pct == 10.0  # 1/10 = 10%
        assert bc3.source_token_aligned_pct == 16.0  # 8/50 = 16%
        assert bc3.source_coverage_pct == 80.0  # Within aligned verses: 8/10 = 80%

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

        bc = BookCoverage(
            book_id="41",
            verse_coverages=[vc],
            source_token_count=15,
            verse_count=2,
        )
        summary = bc.summary()

        assert "Book 41" in summary
        assert "Verses=1/2" in summary  # Updated to match new summary format
        assert "8/10" in summary

    def test_asdict_with_new_fields(self) -> None:
        """Test asdict includes new fields."""
        vc = VerseCoverage(
            bcvid="41001001",
            source_total=10,
            source_aligned=8,
            source_unaligned=2,
            target_total=15,
            target_aligned=12,
            target_unaligned=3,
        )

        bc = BookCoverage(
            book_id="41",
            verse_coverages=[vc],
            source_token_count=20,
            verse_count=5,
        )

        d = bc.asdict()
        assert d["Book_ID"] == "41"
        assert d["Verse_Count"] == 5
        assert d["Verse_Coverage_Pct"] == 20.0  # 1/5 = 20%
        assert d["Source_Tokens"] == 20
        assert d["Source_Token_Aligned_Pct"] == 40.0  # 8/20 = 40%
        assert "Source_Total" in d
        assert "Target_Coverage_Pct" in d


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
