"""Common utility code."""

from dataclasses import dataclass, field
from typing import Optional

from ..burrito import VerseData
from ..burrito.VerseData import DiffRecord


@dataclass
class BCVPair:
    """Manage BCV data from two managers."""

    bcv: str
    mgr1_data: Optional[VerseData] = None
    mgr2_data: Optional[VerseData] = None
    pairing: str = ""
    diffs: Optional[list[DiffRecord]] = field(init=False, default_factory=list[DiffRecord])

    def __post_init__(self) -> None:
        """Initialize an instance."""
        if self.mgr1_data and self.mgr2_data:
            self.pairing = "both"
            self.diffs = self.mgr1_data.diff(self.mgr2_data)
        elif self.mgr1_data:
            self.pairing = "mgr1"
        elif self.mgr2_data:
            self.pairing = "mgr2"
        else:
            self.pairing = "neither"

    def __repr__(self) -> str:
        """Return a printed representation."""
        return f"<BCVPair({self.bcv})>"
