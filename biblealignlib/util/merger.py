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
from ..burrito import AlignmentGroup, AlignmentRecord, Manager, VerseData, write_alignment_group
from ..burrito.util import groupby_bcid
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

    def show_diffs(self) -> None:
        """Display information about overlaps that differ."""
        overlap_bcs = groupby_bcid([bcvp.bcv for bcvp in self.diffpairs])
        print(f"{len(overlap_bcs)} overlapping and different chapters")
        print(overlap_bcs.keys())
        for bcvpair in self.diffpairs:
            vd1 = bcvpair.mgr1_data
            vd2 = bcvpair.mgr2_data
            print(bcvpair.bcv, ": ", len(vd1.alignments), "---", len(vd2.alignments))

    def safe_merge(self) -> AlignmentGroup:
        """Return a new AlignmentGroup merging records where safe."""
        algroup1 = self.mgr1.alignmentsreader.alignmentgroup
        # get the records that only belong to one side
        disjoint1 = [bcv for bcv, bcvp in self.bcv_pairs.items() if bcvp.pairing == "mgr1"]
        disjointrecords: list[AlignmentRecord] = [
            alrec for bcv in disjoint1 for alrec in self.mgr1.bcv["records"][bcv]
        ]
        disjoint2 = [bcv for bcv, bcvp in self.bcv_pairs.items() if bcvp.pairing == "mgr2"]
        disjointrecords += [alrec for bcv in disjoint2 for alrec in self.mgr2.bcv["records"][bcv]]
        return AlignmentGroup(
            documents=algroup1.documents,
            meta=algroup1.meta,
            records=sorted(disjointrecords),
            roles=algroup1.roles,
        )

    def add_records(
        self, algroup: AlignmentGroup, records: tuple[AlignmentRecord, ...]
    ) -> AlignmentGroup:
        """Add records to algroup and return a new AlignmentGroup."""
        # check for any duplication
        recordsdict: dict[str, AlignmentRecord] = {
            recid: record
            for record in algroup.records
            if (recid := "-".join(record.source_selectors))
        }
        for record in records:
            recid = "-".join(record.source_selectors)
            assert recid not in recordsdict, f"Duplicate record {record}"
        return AlignmentGroup(
            documents=algroup.documents,
            meta=algroup.meta,
            records=sorted(algroup.records + list(records)),
            roles=algroup.roles,
        )

    def write_merge(self) -> None:
        """Write the safely-merged AlignmentGroup."""
        newgroup = self.safe_merge()
        alset1 = self.mgr1.alignmentset
        alignmentpath = alset1.alignmentpath
        targetid = alset1.targetid
        sourceid = alset1.sourceid
        newname = alset1.alternateid + self.mgr2.alignmentset.alternateid
        with alignmentpath.with_name(f"{sourceid}-{targetid}-{newname}.json").open("w") as f:
            write_alignment_group(newgroup, f)
