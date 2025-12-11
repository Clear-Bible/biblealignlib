"""Test coverage analyzer."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager
from biblealignlib.coverage import (
    BookCoverage,
    CoverageAnalyzer,
    CoverageFilter,
    GroupCoverage,
    VerseCoverage,
)

ENGLANGDATAPATH = CLEARROOT / "Alignments/data/eng"


@pytest.fixture(scope="module")
def sblgntbsb() -> AlignmentSet:
    """Return AlignmentSet instance."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )


@pytest.fixture(scope="module")
def mgr(sblgntbsb: AlignmentSet) -> Manager:
    """Return Manager instance."""
    return Manager(sblgntbsb)


@pytest.fixture(scope="module")
def analyzer(mgr: Manager) -> CoverageAnalyzer:
    """Return CoverageAnalyzer with default filter."""
    return CoverageAnalyzer(mgr)


@pytest.fixture(scope="module")
def analyzer_content(mgr: Manager) -> CoverageAnalyzer:
    """Return CoverageAnalyzer with content filter."""
    return CoverageAnalyzer(mgr, filter_type=CoverageFilter.CONTENT)


class TestCoverageAnalyzer:
    """Test CoverageAnalyzer class."""

    def test_init(self, analyzer: CoverageAnalyzer) -> None:
        """Test initialization."""
        assert analyzer.filter_type == CoverageFilter.ALL
        assert analyzer.manager.alignmentset.sourceid == "SBLGNT"

    def test_repr(self, analyzer: CoverageAnalyzer) -> None:
        """Test string representation."""
        rep = repr(analyzer)
        assert "CoverageAnalyzer" in rep
        assert "BSB" in rep

    def test_verse_coverage(self, analyzer: CoverageAnalyzer) -> None:
        """Test verse-level coverage computation."""
        # Use Mark 4:3 as test verse
        vc = analyzer.verse_coverage("41004003")
        assert vc is not None
        assert isinstance(vc, VerseCoverage)
        assert vc.bcvid == "41004003"
        assert vc.source_total > 0
        assert vc.target_total > 0
        assert 0 <= vc.source_coverage_pct <= 100
        assert 0 <= vc.target_coverage_pct <= 100

    def test_verse_coverage_none(self, analyzer: CoverageAnalyzer) -> None:
        """Test verse coverage returns None for invalid verse."""
        vc = analyzer.verse_coverage("99999999")
        assert vc is None

    def test_verse_coverage_cache(self, analyzer: CoverageAnalyzer) -> None:
        """Test that verse coverage is cached."""
        vc1 = analyzer.verse_coverage("41004003")
        vc2 = analyzer.verse_coverage("41004003")
        # Should return same object (cached)
        assert vc1 is vc2

    def test_verse_coverage_has_tokens(self, analyzer: CoverageAnalyzer) -> None:
        """Test that verse coverage includes token details."""
        vc = analyzer.verse_coverage("41004003")
        assert len(vc.source_tokens) > 0
        assert len(vc.target_tokens) > 0

    def test_book_coverage(self, analyzer: CoverageAnalyzer) -> None:
        """Test book-level coverage computation."""
        bc = analyzer.book_coverage("41")
        assert isinstance(bc, BookCoverage)
        assert bc.book_id == "41"
        assert len(bc.verse_coverages) > 0
        assert bc.source_total > 0
        assert bc.target_total > 0

    def test_book_coverage_cache(self, analyzer: CoverageAnalyzer) -> None:
        """Test that book coverage is cached."""
        bc1 = analyzer.book_coverage("41")
        bc2 = analyzer.book_coverage("41")
        assert bc1 is bc2

    def test_coverage_all(self, analyzer: CoverageAnalyzer) -> None:
        """Test overall coverage computation."""
        gc = analyzer.coverage_all()
        assert isinstance(gc, GroupCoverage)
        assert gc.identifier == "all"
        assert len(gc.verse_coverages) > 0
        assert len(gc.book_coverages) > 0

    def test_coverage_group(self, analyzer: CoverageAnalyzer) -> None:
        """Test coverage for a group (Mark 4)."""
        gc = analyzer.coverage_group("41004")
        assert gc.identifier == "41004"
        # Should have all verses from Mark 4
        assert all(vc.bcvid.startswith("41004") for vc in gc.verse_coverages)
        assert len(gc.verse_coverages) > 0

    def test_coverage_partial(self, analyzer: CoverageAnalyzer) -> None:
        """Test coverage for a verse range."""
        gc = analyzer.coverage_partial("41001001", "41001010")
        assert gc.identifier == "41001001-41001010"
        assert len(gc.verse_coverages) > 0
        # All verses should be in range
        for vc in gc.verse_coverages:
            assert "41001001" <= vc.bcvid <= "41001010"

    def test_content_filter(
        self, mgr: Manager, analyzer: CoverageAnalyzer, analyzer_content: CoverageAnalyzer
    ) -> None:
        """Test that content filter reduces source counts."""
        vc_all = analyzer.verse_coverage("41004003")
        vc_content = analyzer_content.verse_coverage("41004003")

        # Content filter should have fewer or equal source tokens counted
        assert vc_content.source_total <= vc_all.source_total

    def test_dataframe_verse(self, analyzer: CoverageAnalyzer) -> None:
        """Test DataFrame export at verse level."""
        # Use a small group for testing
        gc = analyzer.coverage_group("41001")
        df = analyzer.dataframe(level="verse", group_coverage=gc)

        assert "BCVID" in df.columns
        assert "Source_Total" in df.columns
        assert "Target_Coverage_Pct" in df.columns
        assert len(df) > 0
        # Should match number of verses
        assert len(df) == len(gc.verse_coverages)

    def test_dataframe_book(self, analyzer: CoverageAnalyzer) -> None:
        """Test DataFrame export at book level."""
        # Use a single book
        gc = analyzer.coverage_group("41")
        df = analyzer.dataframe(level="book", group_coverage=gc)

        assert "Book_ID" in df.columns
        assert "Source_Total" in df.columns
        assert "Num_Verses" in df.columns
        assert len(df) > 0

    def test_dataframe_invalid_level(self, analyzer: CoverageAnalyzer) -> None:
        """Test that invalid level raises ValueError."""
        with pytest.raises(ValueError):
            analyzer.dataframe(level="invalid")

    def test_write_tsv(self, analyzer: CoverageAnalyzer) -> None:
        """Test TSV export."""
        gc = analyzer.coverage_group("41001")

        with NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            outpath = Path(f.name)

        try:
            analyzer.write_tsv(outpath, level="verse", group_coverage=gc)
            assert outpath.exists()
            content = outpath.read_text()
            assert "BCVID" in content
            assert "Source_Total" in content
        finally:
            if outpath.exists():
                outpath.unlink()

    def test_display_unaligned_source(
        self, analyzer: CoverageAnalyzer, capsys: pytest.CaptureFixture
    ) -> None:
        """Test display_unaligned for source tokens."""
        analyzer.display_unaligned("41004003", token_type="source")
        captured = capsys.readouterr()
        assert "Unaligned source tokens" in captured.out

    def test_display_unaligned_target(
        self, analyzer: CoverageAnalyzer, capsys: pytest.CaptureFixture
    ) -> None:
        """Test display_unaligned for target tokens."""
        analyzer.display_unaligned("41004003", token_type="target")
        captured = capsys.readouterr()
        assert "Unaligned target tokens" in captured.out

    def test_display_unaligned_invalid_verse(
        self, analyzer: CoverageAnalyzer, capsys: pytest.CaptureFixture
    ) -> None:
        """Test display_unaligned for invalid verse."""
        analyzer.display_unaligned("99999999", token_type="target")
        captured = capsys.readouterr()
        assert "No coverage data" in captured.out

    def test_display_unaligned_invalid_type(self, analyzer: CoverageAnalyzer) -> None:
        """Test display_unaligned with invalid token_type."""
        with pytest.raises(ValueError):
            analyzer.display_unaligned("41004003", token_type="invalid")


class TestFilters:
    """Test filter functionality."""

    def test_all_filter(self, mgr: Manager) -> None:
        """Test ALL filter counts all tokens."""
        analyzer = CoverageAnalyzer(mgr, filter_type=CoverageFilter.ALL)
        vc = analyzer.verse_coverage("41004003")
        vd = mgr["41004003"]

        # Should count all sources and targets
        assert vc.source_total == len(vd.sources)
        # Note: ALL filter counts all targets, not just targets_included
        assert vc.target_total == len(vd.targets)

    def test_content_filter_sources(self, mgr: Manager) -> None:
        """Test CONTENT filter on sources."""
        analyzer = CoverageAnalyzer(mgr, filter_type=CoverageFilter.CONTENT)
        vc = analyzer.verse_coverage("41004003")
        vd = mgr["41004003"]

        # Should count only content sources
        content_sources = [s for s in vd.sources if s.is_content]
        assert vc.source_total == len(content_sources)

    def test_nonexcluded_filter_targets(self, mgr: Manager) -> None:
        """Test NONEXCLUDED filter on targets."""
        analyzer = CoverageAnalyzer(mgr, filter_type=CoverageFilter.NONEXCLUDED)
        vc = analyzer.verse_coverage("41004003")
        vd = mgr["41004003"]

        # Should count only non-excluded targets
        assert vc.target_total == len(vd.targets_included)
