"""Merge alignment data.

Input is two Manager instances, which must be based on the same
source, target language, and target version.


>>> from biblealignlib.burrito import CLEARROOT, Manager, AlignmentSet
>>> from biblealignlib.util import merger
>>> targetlang, targetid, sourceid = ("hin", "IRVHin", "SBLGNT")
# get manager instances for two sets of alignments
>>> sunilas = AlignmentSet(targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"), alternateid="Sunil")
>>> sunilmgr = Manager(sunilas)
>>> suphinas = AlignmentSet(targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"), alternateid="Suphin")
>>> suphinmgr = Manager(suphinas)
# instantiate a Merger
>>> mergerinst = merger.Merger(sunilmgr, suphinmgr)
# how many of each type of pairing?
>>> mergerinst.pairingcounts
Counter({'neither': 6191, 'mgr1': 1272, 'both': 475, 'mgr2': 1})
# cases where they overlap but have differences
>>> len(mergerinst.diffpairs)
22
>>> mergerinst.diffpairs
[<BCVPair(57001002)>, <BCVPair(57001003)>, <BCVPair(57001004)>, <BCVPair(57001005)>, ... ]
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

# from biblealignlib.burrito import DiffRecord, Manager, VerseData
from ..burrito import Manager, VerseData
from ..burrito.VerseData import DiffRecord


@dataclass
class BCVPair:
    """Manage BCV data from two managers."""

    bcv: str
    mgr1_data: Optional[VerseData] = None
    mgr2_data: Optional[VerseData] = None
    pairing: str = ""
    diffs: Optional[list[DiffRecord]] = field(init=False, default_factory=list)

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


class Merger:

    def __init__(self, mgr1: Manager, mgr2: Manager) -> None:
        """Initialize an instance."""
        self.mgr1 = mgr1
        self.mgr2 = mgr2
        for attr in ("sourceid", "targetlanguage", "targetid"):
            assert getattr(self.mgr1.alignmentset, attr) == getattr(
                self.mgr1.alignmentset, attr
            ), f"Managers must have the same {attr} attribute."
        # should be the same for both
        self.allsrcbcv = mgr1.bcv["sources"]
        self.bcv_pairs = self.get_bcv_pairs()
        self.pairingcounts = Counter(bcvp.pairing for bcvp in self.bcv_pairs.values())
        # overlaps
        self.overlaps = [bcvp for bcvp in self.bcv_pairs.values() if bcvp.pairing == "both"]
        # overlaps with differences
        self.diffpairs = [bcvp for bcvp in self.overlaps if bcvp.diffs]

    def get_bcv_pairs(self) -> dict[str, BCVPair]:
        """Return a dictionary of BCVPair instances."""
        bcv_pairs = {}
        for bcv in self.allsrcbcv:
            bcv_pairs[bcv] = BCVPair(
                bcv, self.mgr1.bcv["versedata"].get(bcv), self.mgr2.bcv["versedata"].get(bcv)
            )
        return bcv_pairs
