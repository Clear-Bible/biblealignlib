"""Test coverage exporter."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager
from biblealignlib.coverage import CoverageAnalyzer, CoverageExporter

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
    """Return CoverageAnalyzer."""
    return CoverageAnalyzer(mgr)


class TestCoverageExporter:
    """Test CoverageExporter class."""

    def test_summary_report(self, analyzer: CoverageAnalyzer) -> None:
        """Test summary report generation."""
        gc = analyzer.coverage_group("41001")
        report = CoverageExporter.summary_report(gc, include_books=True, include_verses=False)

        assert "COVERAGE REPORT" in report
        assert "41001" in report
        assert "OVERALL COVERAGE" in report
        assert "Source:" in report
        assert "Target:" in report

    def test_summary_report_with_verses(self, analyzer: CoverageAnalyzer) -> None:
        """Test summary report with verse details."""
        gc = analyzer.coverage_group("41001")
        report = CoverageExporter.summary_report(gc, include_books=True, include_verses=True)

        assert "BY VERSE:" in report
        # Should have verse IDs
        assert "41001" in report

    def test_write_summary_report(self, analyzer: CoverageAnalyzer) -> None:
        """Test writing summary report to file."""
        gc = analyzer.coverage_group("41001")

        with NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            outpath = Path(f.name)

        try:
            CoverageExporter.write_summary_report(gc, outpath, include_books=True)
            assert outpath.exists()
            content = outpath.read_text()
            assert "COVERAGE REPORT" in content
        finally:
            if outpath.exists():
                outpath.unlink()

    def test_combined_tsv(self, analyzer: CoverageAnalyzer) -> None:
        """Test combined TSV export."""
        gc = analyzer.coverage_group("41")

        with NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            outpath = Path(f.name)

        try:
            CoverageExporter.combined_tsv(gc, outpath)
            assert outpath.exists()
            content = outpath.read_text()
            assert "# VERSE-LEVEL COVERAGE" in content
            assert "# BOOK-LEVEL COVERAGE" in content
            assert "BCVID" in content
            assert "Book_ID" in content
        finally:
            if outpath.exists():
                outpath.unlink()
