"""Common utility code."""

from dataclasses import dataclass, field
from typing import Optional

from ..burrito import DiffRecord, VerseData


@dataclass
class BCVPair:
    """Manage BCV data from two managers."""

    # like "41004003"
    bcv: str
    # VerseData for the first manager
    mgr1_data: Optional[VerseData] = None
    # VerseData for the second manager
    mgr2_data: Optional[VerseData] = None
    # a label for what data is available to the pair: "both", "mgr1",
    # "mgr2", or "neither"
    pairing: str = ""
    # a general list of differences
    diffs: list[DiffRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize an instance."""
        if self.mgr1_data and self.mgr2_data:
            self.pairing = "both"
        elif self.mgr1_data:
            self.pairing = "mgr1"
        elif self.mgr2_data:
            self.pairing = "mgr2"
        else:
            self.pairing = "neither"

    def __repr__(self) -> str:
        """Return a printed representation."""
        return f"<BCVPair({self.bcv})>"
