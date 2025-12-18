"""Configure and run manager to read Burrito alignment data.

Given an alignment set, read the data on file into internal
representations.

This assumes you know what alignment set you're looking for, and that
the data already exists in Scripture Burrito format. Alignment sets
are identified by a language (code), target and source IDs, and a path to the data.

>>> from biblealignlib.burrito import CLEARROOT, Manager, AlignmentSet
# your local copy of alignments-eng/data
>>> targetlang, targetid, sourceid = ("eng", "BSB", "SBLGNT")
>>> alset = AlignmentSet(targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
>>> mgr = Manager(alset)
>>> mgr["40001024"]
<VerseData: 40001024>

# To upgrade older alignments to the latest standard, see
# src.check.Upgrader.write_alignment_group()

"""

from collections import UserDict

from typing import Any, TypedDict, Union

from .AlignmentGroup import AlignmentRecord
from .AlignmentSet import AlignmentSet
from .VerseData import VerseData
from .alignments import AlignmentsReader
from .source import Source, SourceReader
from .target import Target, TargetReader
from .util import groupby_bcv


class BCVData(TypedDict, total=False):
    """Type definition for the bcv dictionary structure.

    total=False allows keys to be added progressively during initialization.
    """

    sources: dict[str, list[Source]]
    targets: dict[str, list[Target]]
    records: dict[str, list[AlignmentRecord]]
    versedata: dict[str, VerseData]


# create a Manager class to read data into AlignmentGroup instances
# and write them out to files
class Manager(UserDict):
    """Manage data read from Burrito files.

    self is a dict of BCV identifiers -> VerseData instances.
    """

    tokentypeattrs: set[str] = {"source", "target"}
    # the keys under self.bcv
    bcvkeys: tuple[str, ...] = ("sources", "targets", "target_sourceverses", "records", "versedata")

    def __init__(
        self,
        alignmentset: AlignmentSet,
        # this probably doesn't belong here
        creator: str = "GrapeCity",
        keeptargetwordpart: bool = False,
        # if True, don't remove bad records
        keepbadrecords: bool = False,
    ) -> None:
        """Initialize a Manager instance for an AlignmentSet.

        With keeptargetwordpart = False (the default), drop a 12th character
        representing the part index for a target token
        ID. keeptargetwordpart does not affect source token identifiers.

        """
        super().__init__()
        self.keeptargetwordpart: bool = keeptargetwordpart
        self.keepbadrecords: bool = keepbadrecords
        # the configuration of alignment data
        self.alignmentset: AlignmentSet = alignmentset
        print(self.alignmentset.displaystr)
        # keys are token identifiers from source/manuscript data
        self.sourceitems: SourceReader = self.read_sources()
        self.targetitems: TargetReader = self.read_targets()
        # several sets of data, all grouped by BCV
        self.bcv: BCVData = {
            # The source and target token readers with the TSV data
            "sources": groupby_bcv(list(self.sourceitems.values())),
            "targets": groupby_bcv(list(self.targetitems.values())),
            # by source_verse attribute: this should coordinate with source
            # maybe unnecessary? at least don't need in init
            # "target_sourceverses": groupby_bcv(
            #     list(self.targetitems.values()),
            #     bcvfn=lambda t: t.source_verse,
            # ),
        }
        # The cleaned AlignmentRecords are in
        # self.alignmentsreader.alignmentgroup
        # used in multiple fns under _clean_alignmentrecord
        self.alignmentsreader: AlignmentsReader = AlignmentsReader(
            alignmentset=alignmentset,
            keeptargetwordpart=self.keeptargetwordpart,
            keepbadrecords=self.keepbadrecords,
        )
        self.alignmentsreader.clean_alignments(self.sourceitems, self.targetitems)
        # group records by BCV
        self.bcv["records"] = groupby_bcv(
            list(self.alignmentsreader.alignmentgroup.records), lambda r: r.source_bcv
        )
        # and make VerseData instances for alignments
        versedata: dict[str, VerseData] = {
            bcvid: self.make_versedata(bcvid) for bcvid in self.bcv["records"]
        }
        self.bcv["versedata"] = versedata
        self.data = self.bcv["versedata"]
        self.check_integrity()

    def __repr__(self) -> str:
        """Return a printed representation."""
        return f"<{self.__class__.__name__} with {len(self)} keys>"

    def read_sources(self) -> SourceReader:
        """Read source data into SourceReader."""
        return SourceReader(self.alignmentset.sourcepath)

    def read_targets(self) -> TargetReader:
        """Read target data into TargetReader."""
        # may need more single-name target files
        return TargetReader(self.alignmentset.targetpath, keepwordpart=self.keeptargetwordpart)

    def make_versedata(
        self,
        bcvid: str,
        # dunno why this param
        # verserecords: dict[str, list[AlignmentRecord]] = {}
    ) -> VerseData:
        """Return a VerseData instance for a BCV reference."""
        # if not verserecords:
        #     # type complaint here that's not easily fixed because of the "bcv" dict
        #     verserecords = self.bcv["records"]
        verserecords = self.bcv["records"]
        # this should not happen
        if bcvid not in verserecords:
            raise ValueError(f"BCV {bcvid} not found in records")
        # pair up the selectors
        alpairs: list[tuple[list[str], list[str]]] = [
            (ardict["source"], ardict["target"])
            for ar in verserecords[bcvid]
            # internal so omit macula prefix
            if (ardict := ar.asdict(withmaculaprefix=False))
        ]
        # make instances from token IDs
        alinstpairs: list[tuple[list[Source], list[Target]]] = [
            (sourceinst, targetinst)
            for sources, targets in alpairs
            # what does it mean if tok isn't in sourceinst?? SBLGNT-BSB data
            # drop tokens. This could silently drop tokens.
            if (sourceinst := [self.sourceitems[tok] for tok in sources])
            if (targetinst := [self.targetitems[tok] for tok in targets])
            # if (sourceinst := [self.sourceitems[tok] for tok in sources if tok in self.sourceitems])
            # if (targetinst := [self.targetitems[tok] for tok in targets if tok in self.targetitems])
        ]
        targets = [target for pair in alinstpairs for target in pair[1]]
        return VerseData(
            bcvid=bcvid,
            alignments=alinstpairs,
            records=tuple(self.bcv["records"][bcvid]),
            sources=self.bcv["sources"].get(bcvid) or [],
            # target BCVID may differ from source BCV! and this is
            # only target tokens that are aligned
            # targets=self.bcv["targets"].get(bcvid) or [],
            targets=targets,
        )

    def display_record(self, record: AlignmentRecord) -> str:
        """Return a string for debugging records."""
        basestr = f"{record.identifier}:"
        # show other attributes besides the token text?
        sources = "\n           ".join(
            [tok.tokenstr for sel in record.source_selectors if (tok := self.sourceitems[sel])]
        )
        basestr += f"\n  Sources: {sources}"
        targets = "\n           ".join(
            [tok.tokenstr for sel in record.target_selectors if (tok := self.targetitems[sel])]
        )
        basestr += f"\n  Targets: {targets}"
        return basestr

    def check_integrity(self) -> None:
        """Check the data and print messages for any problems."""
        if len(self.bcv["records"]) != len(self.bcv["versedata"]):
            print(
                f"{len(self.bcv['records'])} BCV records != {len(self.bcv['versedata'])} VerseData instances."
            )
        if len(self.bcv["sources"]) < len(self.bcv["records"]):
            print(f"{len(self.bcv['sources'])} BCV sources < {len(self.bcv['records'])} records.")

    def get_source_alignments(self) -> set[Source]:
        """Return the set of sources that are aligned."""
        return {
            s
            for bcvid in self.bcv["versedata"]
            for al in self.bcv["versedata"][bcvid].alignments
            if (sources := al[0])
            for s in sources
        }

    def get_target_alignments(self) -> dict[Target, Source]:
        """Get the target-to-source alignment mapping for all aligned targets."""
        return {
            t: s
            for bcvid in self.bcv["versedata"]
            for al in self.bcv["versedata"][bcvid].alignments
            if (sources := al[0])
            if (targets := al[1])
            for s in sources
            for t in targets
        }

    def token_alignments(
        self, term: str, role: str = "source", tokenattr: str = "text", lowercase: bool = False
    ) -> list[AlignmentRecord]:
        """Return a list of alignments whose role tokens contain term."""
        itemreader: SourceReader | TargetReader = (
            self.sourceitems if role == "source" else self.targetitems
        )
        tokendict: dict[str, Source | Target] = {
            token.id: token
            for token in itemreader.term_tokens(term, tokenattr=tokenattr, lowercase=lowercase)
        }
        selectorset = set(tokendict)
        # collect alignment records that contain these tokens
        selectorattr = "source_selectors" if role == "source" else "target_selectors"
        token_records = [
            rec
            for rec in self.alignmentsreader.alignmentgroup.records
            if selectorset.intersection(getattr(rec, selectorattr))
        ]
        return token_records
