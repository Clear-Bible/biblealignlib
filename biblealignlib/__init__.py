"""Internal-only code for working with alignment data."""

from enum import Enum
import os
from pathlib import Path
import re

import dotenv

from .strongs import normalize_strongs

# set path variables. These assume you have a .env file that locates
# the directory where Clear-Bible repositories are located, like
#
# CLEARROOT=/Users/sboisen/git/Clear-Bible
#
# use an environment variable if
if not dotenv.load_dotenv():
    print("No .env file found")
clearrootenvar = os.getenv("CLEARROOT")
if clearrootenvar:
    CLEARROOT = Path(clearrootenvar)
else:
    CLEARROOT = Path.home() / "git/Clear-Bible"
    print(f"No environment variable for CLEARROOT: assuming {CLEARROOT}")

# for loading published data. Alignments are here under language
ALIGNMENTSDATA = CLEARROOT / "Alignments/data"
# for loading published source TSVs
SOURCES = ALIGNMENTSDATA / "sources"

CANONIDS = {
    "nt",
    "ot",
    # meaning the entire 66 book corpus
    "protestant",
}


VERSIFICATIONIDS: set[str] = {
    "eng",
    "org",
    "rso",
    # not yet implemented
    # "ethiopian_custom", "lxx", "rsc", "vul"
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


def get_canonid(bcv: str) -> str:
    """Return nt/ot for a BCVish string.

    Simple string matching on the book portion of an identifier, so
    works for books, chapters, verses and full BCVWPID identifiers.

    """
    otcanonre = re.compile(r"^[0-3][0-9]")
    ntcanonre = re.compile(r"^[4-6][0-9]")
    # don't include 67-69
    notntcanonre = re.compile(r"^6[7-9]")
    if otcanonre.match(bcv):
        return "ot"
    elif ntcanonre.match(bcv) and not notntcanonre.match(bcv):
        return "nt"
    else:
        raise ValueError(f"Invalid BCVish id value: {bcv}")


__all__ = [
    "CLEARROOT",
    "SOURCES",
    "SourceidEnum",
    # strongs
    "normalize_strongs",
]
