"""Filter enums and helper functions for coverage analysis."""

from enum import Enum
from typing import Callable

from biblealignlib.burrito import Source, Target


class CoverageFilter(str, Enum):
    """Enumerate filter types for coverage analysis."""

    ALL = "all"  # Count all tokens
    CONTENT = "content"  # Source: is_content only; Target: non-excluded
    # this needs more work
    # NAME = "name"  # Source: pos == 'Name'; Target: non-excluded
    NONEXCLUDED = "nonexcluded"  # Target: non-excluded only; Source: all
    CONTENT_NONEXCLUDED = "content_nonexcluded"  # Intersection of both

    @property
    def description(self) -> str:
        """Return human-readable description."""
        return {
            "all": "All tokens (sources and targets)",
            "content": "Content words only (noun/verb/adj/adv sources, non-excluded targets)",
            # "name": "Names only, with non-excluded targets",
            "nonexcluded": "Non-excluded targets only (all sources)",
            "content_nonexcluded": "Content sources and non-excluded targets",
        }[self.value]


def get_source_filter(filter_type: CoverageFilter) -> Callable[[Source], bool]:
    """Return filter function for source tokens.

    Returns a function that takes a Source token and returns True if it should be counted.
    """
    if filter_type in (CoverageFilter.ALL, CoverageFilter.NONEXCLUDED):
        return lambda src: True
    elif filter_type in (CoverageFilter.CONTENT, CoverageFilter.CONTENT_NONEXCLUDED):
        return lambda src: src.is_content
    # elif filter_type in (CoverageFilter.NAME):
    #     return lambda src: src.pos == "Name"
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")


def get_target_filter(filter_type: CoverageFilter) -> Callable[[Target], bool]:
    """Return filter function for target tokens.

    Returns a function that takes a Target token and returns True if it should be counted.
    """
    if filter_type == CoverageFilter.ALL:
        return lambda trg: True
    elif filter_type in (
        CoverageFilter.CONTENT,
        # CoverageFilter.NAME,
        CoverageFilter.NONEXCLUDED,
        CoverageFilter.CONTENT_NONEXCLUDED,
    ):
        return lambda trg: not trg.exclude
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")
