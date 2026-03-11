from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .source import Source
from .target import Target


class DiffReason(Enum):
    """Enumerate constants for alignment differences."""

    DIFFLEN = "Different number of alignments"
    DIFFSOURCES = "Source selectors differ"
    DIFFTARGETS = "Target selectors differ"
    DIFFNOTES = "Different notes"
    DIFFSTATUS = "Different status"


@dataclass
class DiffRecord:
    """Container for data on alignment differences for a verse.

    The same verse could have multiple alignment differences.
    """

    # the alignment BCV
    bcvid: str
    # the data in the first alignment
    sources1: tuple[Source, ...] = ()
    targets1: tuple[Target, ...] = ()
    # the data in the second alignment
    sources2: tuple[Source, ...] = ()
    targets2: tuple[Target, ...] = ()
    # why it's different
    diffreason: Optional[DiffReason] = None
    # any auxiliary data
    data: tuple = ()

    def __repr__(self) -> str:
        """Return a string representation."""
        basestr = (
            f"<DiffRecord ({self.bcvid}): '{self.diffreason.value if self.diffreason else None}'"
        )
        if self.data:
            basestr += ", " + repr(self.data)
        basestr += ">"
        return basestr
