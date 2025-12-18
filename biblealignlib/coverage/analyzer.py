"""Coverage analyzer for alignment data.

Example usage:

>>> from biblealignlib.burrito import Manager, AlignmentSet
>>> from biblealignlib.coverage import CLEARROOT, CoverageAnalyzer, CoverageFilter
>>>
>>> # Create manager
>>> targetlang = "eng"
>>> alset = AlignmentSet(sourceid="SBLGNT", targetid="BSB",
...                      targetlanguage=targetlang,
...                      langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
>>> mgr = Manager(alset)
>>>
>>> # Analyze coverage with default filter (all tokens)
>>> analyzer = CoverageAnalyzer(mgr)
>>>
>>> # Get verse coverage
>>> verse_cov = analyzer.verse_coverage("41004003")
>>> print(verse_cov.summary())
>>>
>>> # Get book coverage
>>> book_cov = analyzer.book_coverage("41")
>>> print(book_cov.summary())
>>>
>>> # Get overall coverage
>>> all_cov = analyzer.coverage_all()
>>> print(all_cov.summary())
>>>
>>> # get coverage for all books
>>> all_books_cov = [analyzer.book_coverage(book) for book in mgr.sourceitems.book_token_counts()]
>>> for book in all_books_cov: print(book.summary())
...
Book 40: S=9339/15267 (61.2%) T=13886/19660 (70.6%)
Book 41: S=7892/11248 (70.2%) T=10679/14919 (71.6%)
Book 42: S=8825/19208 (45.9%) T=12047/25537 (47.2%)
...
>>> # Export to DataFrame
>>> df = analyzer.dataframe(level="verse")
>>>
>>> # Export to TSV
>>> analyzer.write_tsv(outpath=alset.alignmentpath.parent / f"{alset.identifier}.coverage.tsv")
>>>
>>> # Apply content-only filter
# 2025-12-15 sboisen: not sure this is working correctly yet
>>> analyzer_content = CoverageAnalyzer(mgr, filter_type=CoverageFilter.CONTENT)
>>> content_cov = analyzer_content.coverage_all()
>>> print(content_cov.summary())
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from biblealignlib.burrito import Manager, Source, Target, VerseData, util

from .Coverage import BookCoverage, GroupCoverage, TokenCoverage, VerseCoverage
from .filters import CoverageFilter, get_source_filter, get_target_filter


class CoverageAnalyzer:
    """Analyze alignment coverage for a Manager instance.

    Similar to scorer.ScoreCondition pattern - takes Manager as input,
    provides various coverage analysis methods.
    """

    def __init__(self, manager: Manager, filter_type: CoverageFilter = CoverageFilter.ALL) -> None:
        """Initialize coverage analyzer.

        Args:
            manager: Manager instance with loaded alignment data
            filter_type: How to filter tokens (all, content, nonexcluded, etc.)
        """
        self.manager = manager
        self.filter_type = filter_type
        self.source_filter = get_source_filter(filter_type)
        self.target_filter = get_target_filter(filter_type)
        self.source_token_counts: dict[str, int] = self.manager.sourceitems.book_token_counts()
        self.book_verse_counts: dict[str, int] = self.manager.sourceitems.book_verse_counts()

        # Cache for computed coverages
        self._verse_cache: dict[str, VerseCoverage] = {}
        self._book_cache: dict[str, BookCoverage] = {}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<CoverageAnalyzer: {self.manager.alignmentset.targetid}, filter={self.filter_type.value}>"

    def _compute_token_coverage(
        self, versedata: VerseData
    ) -> tuple[list[TokenCoverage], list[TokenCoverage]]:
        """Compute token-level coverage for a verse.

        Returns:
            Tuple of (source_token_coverages, target_token_coverages)
        """
        # Create TokenCoverage for sources
        source_coverages = [
            TokenCoverage(
                token_id=src.id,
                token=src,
                is_aligned=(src in versedata.aligned_sources),
                should_count=self.source_filter(src),
            )
            for src in versedata.sources
        ]

        # Create TokenCoverage for targets (use targets_included for filtering)
        target_coverages = [
            TokenCoverage(
                token_id=trg.id,
                token=trg,
                is_aligned=(trg in versedata.aligned_targets),
                should_count=self.target_filter(trg),
            )
            for trg in versedata.targets
        ]

        return source_coverages, target_coverages

    def verse_coverage(self, bcvid: str) -> Optional[VerseCoverage]:
        """Compute coverage for a single verse.

        Returns None if verse not found in manager.
        """
        assert isinstance(bcvid, str) and len(bcvid) == 8, "bcvid must be an eight-character string"
        # Check cache
        if bcvid in self._verse_cache:
            return self._verse_cache[bcvid]

        # Get verse data
        if bcvid not in self.manager:
            return None

        vd = self.manager[bcvid]

        # Compute token-level coverage
        source_tokens, target_tokens = self._compute_token_coverage(vd)

        # Filter for counting
        source_counted = [tc for tc in source_tokens if tc.should_count]
        target_counted = [tc for tc in target_tokens if tc.should_count]

        # Compute statistics
        source_total = len(source_counted)
        source_aligned = sum(1 for tc in source_counted if tc.is_aligned)
        target_total = len(target_counted)
        target_aligned = sum(1 for tc in target_counted if tc.is_aligned)

        # Create VerseCoverage
        verse_cov = VerseCoverage(
            bcvid=bcvid,
            source_total=source_total,
            source_aligned=source_aligned,
            source_unaligned=(source_total - source_aligned),
            target_total=target_total,
            target_aligned=target_aligned,
            target_unaligned=(target_total - target_aligned),
            source_tokens=source_tokens,
            target_tokens=target_tokens,
        )

        # Cache and return
        self._verse_cache[bcvid] = verse_cov
        return verse_cov

    def _verses_for_book(self, book_id: str) -> list[str]:
        """Return list of BCVIDs for a book.

        Args:
            book_id: Two-character book ID (e.g., "41")
        """
        return [bcv for bcv in self.manager.keys() if bcv.startswith(book_id)]

    def book_coverage(self, book_id: str) -> BookCoverage:
        """Compute coverage for an entire book.

        Args:
            book_id: Two-character book ID (e.g., "41" for Mark)
        """
        assert (
            isinstance(book_id, str) and len(book_id) == 2
        ), "book_id must be a two-character string"
        # Check cache
        if book_id in self._book_cache:
            return self._book_cache[book_id]

        # Get all verses in book
        verse_bcvs = self._verses_for_book(book_id)

        # Compute verse coverages
        verse_coverages = [vc for bcv in verse_bcvs if (vc := self.verse_coverage(bcv))]

        # Create BookCoverage
        book_cov = BookCoverage(
            book_id=book_id,
            verse_coverages=verse_coverages,
            source_token_count=self.source_token_counts.get(book_id, 0),
            verse_count=self.book_verse_counts.get(book_id, 0),
        )

        # Cache and return
        self._book_cache[book_id] = book_cov
        return book_cov

    def coverage_group(self, identifier: str) -> GroupCoverage:
        """Compute coverage for verses starting with identifier.

        Args:
            identifier: Prefix string (e.g., "41" for all of Mark, "41004" for Mark 4)
        """
        verse_bcvs = [bcv for bcv in self.manager.keys() if bcv.startswith(identifier)]

        verse_coverages = [vc for bcv in verse_bcvs if (vc := self.verse_coverage(bcv))]

        # Group by book for book_coverages
        book_ids = sorted(set(bcv[:2] for bcv in verse_bcvs))
        book_coverages = [self.book_coverage(bid) for bid in book_ids]

        return GroupCoverage(
            identifier=identifier,
            verse_coverages=verse_coverages,
            book_coverages=book_coverages,
        )

    def coverage_partial(self, startbcv: str, endbcv: str) -> GroupCoverage:
        """Compute coverage for a range of verses.

        Args:
            startbcv: Starting verse (inclusive)
            endbcv: Ending verse (inclusive)
        """
        # Use util.filter_by_bcv pattern
        partial_bcvs = util.filter_by_bcv(
            list(self.manager.keys()), startbcv=startbcv, endbcv=endbcv
        )

        verse_coverages = [vc for bcv in partial_bcvs if (vc := self.verse_coverage(bcv))]

        # Group by book
        book_ids = sorted(set(bcv[:2] for bcv in partial_bcvs))
        book_coverages = [self.book_coverage(bid) for bid in book_ids]

        return GroupCoverage(
            identifier=f"{startbcv}-{endbcv}",
            verse_coverages=verse_coverages,
            book_coverages=book_coverages,
        )

    def coverage_all(self) -> GroupCoverage:
        """Compute coverage for all verses in manager."""
        all_bcvs = list(self.manager.keys())

        verse_coverages = [vc for bcv in all_bcvs if (vc := self.verse_coverage(bcv))]

        # Group by book
        book_ids = sorted(set(bcv[:2] for bcv in all_bcvs))
        book_coverages = [self.book_coverage(bid) for bid in book_ids]

        return GroupCoverage(
            identifier="all", verse_coverages=verse_coverages, book_coverages=book_coverages
        )

    def dataframe(
        self, level: str = "verse", group_coverage: Optional[GroupCoverage] = None
    ) -> pd.DataFrame:
        """Return DataFrame of coverage data.

        Args:
            level: "verse" or "book" level aggregation
            group_coverage: Optional pre-computed GroupCoverage; if None, uses coverage_all()

        Returns:
            DataFrame with coverage metrics
        """
        if group_coverage is None:
            group_coverage = self.coverage_all()

        if level == "verse":
            rows = [vc.asdict() for vc in group_coverage.verse_coverages]
        elif level == "book":
            rows = [bc.asdict() for bc in group_coverage.book_coverages]
        else:
            raise ValueError(f"Invalid level: {level}. Must be 'verse' or 'book'")

        return pd.DataFrame(rows)

    def write_tsv(
        self, outpath: Path, level: str = "book", group_coverage: Optional[GroupCoverage] = None
    ) -> None:
        """Write coverage data to TSV file.

        Args:
            outpath: Path to output TSV file
            level: "verse" or "book" level aggregation
            group_coverage: Optional pre-computed GroupCoverage; if None, uses coverage_all()
        """
        df = self.dataframe(level=level, group_coverage=group_coverage)
        df.to_csv(outpath, sep="\t", index=False)

    def display_unaligned(self, bcvid: str, token_type: str = "target") -> None:
        """Display unaligned tokens for a verse.

        Similar to VerseData.unaligned() method.

        Args:
            bcvid: Verse identifier
            token_type: "source" or "target"
        """
        verse_cov = self.verse_coverage(bcvid)
        if not verse_cov:
            print(f"No coverage data for {bcvid}")
            return

        if token_type == "source":
            tokenattr = "source_tokens"
        elif token_type == "target":
            tokenattr = "target_tokens"
        else:
            raise ValueError(f"Invalid token_type: {token_type}")
        tokens = [
            tc for tc in getattr(verse_cov, tokenattr) if tc.should_count and not tc.is_aligned
        ]

        print(f"Unaligned {token_type} tokens in {bcvid}:")
        for tc in tokens:
            print(f"  {tc.token_id}: {tc.text}")


# BLOCKED work in progress: see
# https://github.com/Clear-Bible/biblealignlib/tree/main/notebooks/coverage
# for analysis

# class NameSimilarityAnalyzer(CoverageAnalyzer):
#     """Analyze the similarity of aligned name tokens for a Manager instance.

#     Similarity is computed using Levenshtein distance ratio for
#     alignments that pass the filter: by default, this is source tokens
#     whose part of speech == 'Name', only where the target is not
#     excluded.

#     """

#     def __init__(self, manager: Manager, filter_type: CoverageFilter = CoverageFilter.NAME) -> None:
#         """Initialize coverage analyzer.

#         Args:
#             manager: Manager instance with loaded alignment data
#             filter_type: How to filter tokens (all, content, nonexcluded, etc.)
#         """
#         super().__init__(manager, filter_type)

#     def _compute_token_coverage(
#         self, versedata: VerseData
#     ) -> tuple[list[TokenCoverage], list[TokenCoverage]]:
#         """Compute token-level coverage for a verse.

#         Returns:
#             Tuple of (source_token_coverages, target_token_coverages)
#         """
#         # Create TokenCoverage for sources
#         source_coverages = [
#             TokenCoverage(
#                 token_id=src.id,
#                 token=src,
#                 is_aligned=(src in versedata.aligned_sources),
#                 should_count=self.source_filter(src),
#             )
#             for src in versedata.sources
#         ]

#         # Create TokenCoverage for targets (use targets_included for filtering)
#         target_coverages = [
#             TokenCoverage(
#                 token_id=trg.id,
#                 token=trg,
#                 is_aligned=(trg in versedata.aligned_targets),
#                 should_count=self.target_filter(trg),
#             )
#             for trg in versedata.targets
#         ]

#         return source_coverages, target_coverages
