"""Export utilities for coverage data.

Provides additional export formats beyond basic TSV/DataFrame.
"""

from pathlib import Path

import pandas as pd

from .Coverage import GroupCoverage


class CoverageExporter:
    """Export coverage data in various formats."""

    @staticmethod
    def summary_report(
        group_coverage: GroupCoverage,
        include_books: bool = True,
        include_verses: bool = False,
    ) -> str:
        """Generate human-readable summary report.

        Args:
            group_coverage: Coverage data to summarize
            include_books: Include per-book breakdowns
            include_verses: Include per-verse breakdowns (can be verbose)

        Returns:
            Multi-line string report
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"COVERAGE REPORT: {group_coverage.identifier}")
        lines.append("=" * 70)
        lines.append("")

        # Overall summary
        lines.append("OVERALL COVERAGE:")
        lines.append(
            f"  Source: {group_coverage.source_aligned}/{group_coverage.source_total} tokens ({group_coverage.source_coverage_pct:.2f}%)"
        )
        lines.append(
            f"  Target: {group_coverage.target_aligned}/{group_coverage.target_total} tokens ({group_coverage.target_coverage_pct:.2f}%)"
        )
        lines.append(f"  Total verses: {len(group_coverage.verse_coverages)}")
        lines.append("")

        # Book-level summaries
        if include_books and group_coverage.book_coverages:
            lines.append("BY BOOK:")
            lines.append("-" * 70)
            for bc in group_coverage.book_coverages:
                lines.append(bc.summary())
            lines.append("")

        # Verse-level summaries
        if include_verses:
            lines.append("BY VERSE:")
            lines.append("-" * 70)
            for vc in group_coverage.verse_coverages:
                lines.append(vc.summary(brief=True))
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    @staticmethod
    def write_summary_report(
        group_coverage: GroupCoverage,
        outpath: Path,
        include_books: bool = True,
        include_verses: bool = False,
    ) -> None:
        """Write summary report to text file."""
        report = CoverageExporter.summary_report(
            group_coverage, include_books=include_books, include_verses=include_verses
        )
        outpath.write_text(report)

    @staticmethod
    def combined_tsv(group_coverage: GroupCoverage, outpath: Path) -> None:
        """Write TSV with both verse and book levels combined.

        Creates a TSV with separate sections for verse-level and book-level data.
        """
        with outpath.open("w") as f:
            # Write verse-level data
            f.write("# VERSE-LEVEL COVERAGE\n")
            verse_df = pd.DataFrame([vc.asdict() for vc in group_coverage.verse_coverages])
            verse_df.to_csv(f, sep="\t", index=False)

            f.write("\n")

            # Write book-level data
            f.write("# BOOK-LEVEL COVERAGE\n")
            book_df = pd.DataFrame([bc.asdict() for bc in group_coverage.book_coverages])
            book_df.to_csv(f, sep="\t", index=False)
