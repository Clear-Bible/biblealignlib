"""Internal-only code for working with alignment data."""

from enum import Enum
from pathlib import Path

from .strongs import normalize_strongs


ROOT = Path(__file__).parent
DATAPATH = ROOT / "data"
SRCPATH = ROOT / "src"


CANONIDS = {
    "nt",
    "ot",
    # meaning the entire 66 book corpus
    "protestant",
}


class SourceidEnum(str, Enum):
    """Valid source identifiers."""

    BGNT = "BGNT"
    NA27 = "NA27"
    NA28 = "NA28"
    SBLGNT = "SBLGNT"
    WLC = "WLC"
    WLCM = "WLCM"

    @property
    def canon(self) -> str:
        """Return 'ot' or 'nt' for the canon."""
        if self.value in ["WLC", "WLCM"]:
            return "ot"
        elif self.value in ["BGNT", "NA27", "NA28", "SBLGNT"]:
            return "nt"
        else:
            raise ValueError(f"Unknown error in SourceidEnum.canon for {self.value}")

    # need to add DC, probably others down the road
    @staticmethod
    def get_canon(sourceid: str) -> str:
        """Return a canon string for recognized sources, else 'X'."""
        try:
            srcenum = SourceidEnum(sourceid)
            return srcenum.canon
        except ValueError:
            # unrecognized source
            return "X"


__all__ = [
    "ROOT",
    "DATAPATH",
    "SRCPATH",
    "SourceidEnum",
    # strongs
    "normalize_strongs",
]
