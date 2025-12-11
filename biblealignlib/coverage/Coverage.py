"""Dataclasses for alignment coverage metrics."""

from dataclasses import dataclass, field
from typing import Any

from biblelib.word import BCVID

from biblealignlib.burrito import Source, Target


@dataclass
class TokenCoverage:
    """Coverage data for a single token.

    Tracks whether a token (source or target) is aligned or unaligned.
    """

    token_id: str
    token: Source | Target
    is_aligned: bool
    # whether this token should be counted (respects filters)
    should_count: bool = True

    def __repr__(self) -> str:
        """Return a string representation."""
        status = "aligned" if self.is_aligned else "unaligned"
        return f"<TokenCoverage: {self.token_id} ({status})>"

    @property
    def text(self) -> str:
        """Return token text."""
        return self.token.text

    @property
    def bcv(self) -> str:
        """Return BCV identifier."""
        return self.token.to_bcv()


@dataclass
class VerseCoverage:
    """Coverage statistics for a single verse.

    Tracks both source and target coverage separately. Note this only
    includes verses that have alignment data, which may be a subset of
    all verses.

    """

    bcvid: str
    # Source coverage
    source_total: int = 0
    source_aligned: int = 0
    source_unaligned: int = 0
    source_coverage_pct: float = 0.0
    # Target coverage
    target_total: int = 0
    target_aligned: int = 0
    target_unaligned: int = 0
    target_coverage_pct: float = 0.0
    # Token-level details
    source_tokens: list[TokenCoverage] = field(default_factory=list)
    target_tokens: list[TokenCoverage] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Compute percentages after initialization."""
        self.source_coverage_pct = (
            (self.source_aligned / self.source_total * 100) if self.source_total else 0.0
        )
        self.target_coverage_pct = (
            (self.target_aligned / self.target_total * 100) if self.target_total else 0.0
        )

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"<VerseCoverage: {self.bcvid}>"

    def summary(self, brief: bool = True) -> str:
        """Return human-readable summary.

        Example: "41004003: S=12/15 (80.0%) T=18/20 (90.0%)"
        """
        if brief:
            return (
                f"{self.bcvid}: "
                f"S={self.source_aligned}/{self.source_total} ({self.source_coverage_pct:.1f}%) "
                f"T={self.target_aligned}/{self.target_total} ({self.target_coverage_pct:.1f}%)"
            )
        else:
            return (
                f"{self.bcvid}:\n"
                f"  Source: {self.source_aligned}/{self.source_total} aligned ({self.source_coverage_pct:.1f}%)\n"
                f"  Target: {self.target_aligned}/{self.target_total} aligned ({self.target_coverage_pct:.1f}%)"
            )

    def asdict(self, ndigits: int = 2) -> dict[str, Any]:
        """Return dict usable as DataFrame row."""
        return {
            "BCVID": self.bcvid,
            "Verse": self.bcvid[5:],
            "Chapter": self.bcvid[:5],
            "Book": self.bcvid[:2],
            "Reference": BCVID(self.bcvid).to_usfm(),
            "Source_Total": self.source_total,
            "Source_Aligned": self.source_aligned,
            "Source_Unaligned": self.source_unaligned,
            "Source_Coverage_Pct": round(self.source_coverage_pct, ndigits),
            "Target_Total": self.target_total,
            "Target_Aligned": self.target_aligned,
            "Target_Unaligned": self.target_unaligned,
            "Target_Coverage_Pct": round(self.target_coverage_pct, ndigits),
        }


@dataclass
class BookCoverage:
    """Coverage statistics aggregated by book.

    Aggregates verse-level coverage for an entire book.
    """

    book_id: str  # Two-char book ID (e.g., "41" for Mark)
    verse_coverages: list[VerseCoverage] = field(default_factory=list)
    # how many tokens in the book (regardless of alignment)
    source_token_count: int = 0
    # how many of the total are aligned
    source_token_aligned_pct: float = 0.0
    # how many verses in the book (regardless of alignment)
    verse_count: int = 0
    # how many of the verses have any alignments
    verses_with_alignments: int = 0
    verse_coverage_pct: float = 0.0
    # Aggregated source coverage
    source_total: int = 0
    source_aligned: int = 0
    source_unaligned: int = 0
    source_coverage_pct: float = 0.0
    # Aggregated target coverage
    target_total: int = 0
    target_aligned: int = 0
    target_unaligned: int = 0
    target_coverage_pct: float = 0.0

    def __post_init__(self) -> None:
        """Compute aggregates from verse coverages."""
        if self.verse_coverages:
            self.verses_with_alignments = len(self.verse_coverages)
            assert (
                self.verse_count >= self.verses_with_alignments
            ), "Verse count less than verses with alignments"
            # Sum up all verse totals
            self.source_total = sum(v.source_total for v in self.verse_coverages)
            assert (
                self.source_token_count >= self.source_total
            ), "Source token count less than total aligned tokens"
            self.source_aligned = sum(v.source_aligned for v in self.verse_coverages)
            self.source_unaligned = sum(v.source_unaligned for v in self.verse_coverages)
            self.target_total = sum(v.target_total for v in self.verse_coverages)
            self.target_aligned = sum(v.target_aligned for v in self.verse_coverages)
            self.target_unaligned = sum(v.target_unaligned for v in self.verse_coverages)

            # Compute percentages
            self.source_token_aligned_pct = (
                self.source_aligned / self.source_token_count * 100
                if self.source_token_count
                else 0.0
            )
            self.verse_coverage_pct = (
                self.verses_with_alignments / self.verse_count * 100 if self.verse_count else 0.0
            )
            self.source_coverage_pct = (
                (self.source_aligned / self.source_total * 100) if self.source_total else 0.0
            )
            self.target_coverage_pct = (
                (self.target_aligned / self.target_total * 100) if self.target_total else 0.0
            )

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"<BookCoverage: {self.book_id}>"

    def summary(self) -> str:
        """Return human-readable summary."""
        return (
            f"Book {self.book_id}: "
            f"Verses={self.verses_with_alignments}/{self.verse_count} ({self.verse_coverage_pct:.1f}%) "
            f"S={self.source_aligned}/{self.source_total} ({self.source_coverage_pct:.1f}%) "
            f"T={self.target_aligned}/{self.target_total} ({self.target_coverage_pct:.1f}%)"
        )

    def asdict(self, ndigits: int = 2) -> dict[str, Any]:
        """Return dict usable as DataFrame row."""
        return {
            "Book_ID": self.book_id,
            "Verse_Count": self.verse_count,
            "Verse_Coverage_Pct": round(self.verse_coverage_pct, ndigits),
            "Source_Tokens": self.source_token_count,
            "Source_Token_Aligned_Pct": round(self.source_token_aligned_pct, ndigits),
            "Source_Total": self.source_total,
            "Source_Aligned": self.source_aligned,
            "Source_Unaligned": self.source_unaligned,
            "Source_Coverage_Pct": round(self.source_coverage_pct, ndigits),
            "Target_Total": self.target_total,
            "Target_Aligned": self.target_aligned,
            "Target_Unaligned": self.target_unaligned,
            "Target_Coverage_Pct": round(self.target_coverage_pct, ndigits),
            "Num_Verses": len(self.verse_coverages),
        }


@dataclass
class GroupCoverage:
    """Coverage statistics for a group of verses or entire corpus.

    Similar to GroupScore pattern from autoalign.
    """

    identifier: str  # "all", book ID, or custom range
    verse_coverages: list[VerseCoverage] = field(default_factory=list)
    book_coverages: list[BookCoverage] = field(default_factory=list)
    # Overall aggregated metrics
    source_total: int = 0
    source_aligned: int = 0
    source_unaligned: int = 0
    source_coverage_pct: float = 0.0
    target_total: int = 0
    target_aligned: int = 0
    target_unaligned: int = 0
    target_coverage_pct: float = 0.0

    def __post_init__(self) -> None:
        """Compute aggregates."""
        assert self.identifier, "Must provide identifier"
        assert self.verse_coverages, "Must provide verse_coverages"

        # Aggregate from verses
        self.source_total = sum(v.source_total for v in self.verse_coverages)
        self.source_aligned = sum(v.source_aligned for v in self.verse_coverages)
        self.source_unaligned = sum(v.source_unaligned for v in self.verse_coverages)
        self.target_total = sum(v.target_total for v in self.verse_coverages)
        self.target_aligned = sum(v.target_aligned for v in self.verse_coverages)
        self.target_unaligned = sum(v.target_unaligned for v in self.verse_coverages)

        # Compute percentages
        self.source_coverage_pct = (
            (self.source_aligned / self.source_total * 100) if self.source_total else 0.0
        )
        self.target_coverage_pct = (
            (self.target_aligned / self.target_total * 100) if self.target_total else 0.0
        )

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"<GroupCoverage: {self.identifier}>"

    def summary(self) -> str:
        """Return human-readable summary."""
        return (
            f"{self.identifier}: "
            f"S={self.source_aligned}/{self.source_total} ({self.source_coverage_pct:.1f}%) "
            f"T={self.target_aligned}/{self.target_total} ({self.target_coverage_pct:.1f}%)"
        )

    def summary_dict(self, width: int = 2) -> dict[str, str]:
        """Return dict with summary metrics."""
        return {
            "Source_Coverage": f"{self.source_coverage_pct:.{width}f}%",
            "Source_Aligned": str(self.source_aligned),
            "Source_Total": str(self.source_total),
            "Target_Coverage": f"{self.target_coverage_pct:.{width}f}%",
            "Target_Aligned": str(self.target_aligned),
            "Target_Total": str(self.target_total),
        }

    def asdict(self, ndigits: int = 2) -> dict[str, Any]:
        """Return dict usable as DataFrame row."""
        return {
            "Identifier": self.identifier,
            "Source_Total": self.source_total,
            "Source_Aligned": self.source_aligned,
            "Source_Unaligned": self.source_unaligned,
            "Source_Coverage_Pct": round(self.source_coverage_pct, ndigits),
            "Target_Total": self.target_total,
            "Target_Aligned": self.target_aligned,
            "Target_Unaligned": self.target_unaligned,
            "Target_Coverage_Pct": round(self.target_coverage_pct, ndigits),
            "Num_Verses": len(self.verse_coverages),
            "Num_Books": len(self.book_coverages),
        }
