"""Generate integrated data for interlinears/reverse-interlinears (as done for YWAM).

>>> from biblealignlib.burrito import CLEARROOT, Manager, AlignmentSet
>>> from biblealignlib.interlinear.reverse import Reader, Writer
>>> targetlang, targetid, sourceid = ("eng", "BSB", "SBLGNT")
>>> bsbas = AlignmentSet(targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
>>> bsbmgr = Manager(bsbas)
>>> rd = Reader(bsbmgr)
# write it out
>>> wr = Writer(rd)
>>> wr.write(CLEARROOT / "alignments-eng/data/YWAM_share/NIV11" / "SBLGNT-NIV11-aligned.tsv")

"""

from collections import UserDict
from csv import DictWriter
from pathlib import Path

from ..burrito import Manager, VerseData

from .token import AlignedToken


# this might should join in the full Macula data, not just what's in
# the alignments. That would provide Louw-Nida numbers, subjref,
# referent, etc.
class Reader(UserDict):
    """Read alignment data for creating reverse interlinear data."""

    def __init__(self, mgr: Manager) -> None:
        """Initialize an instance."""
        super().__init__(self)
        self.mgr = mgr
        self.aligned_sources: dict[str, set[str]] = {}
        self.target_alignments: dict[str, dict[str, str]] = {}
        # make a target-side dict of alignments
        for bcv, vd in self.mgr.bcv["versedata"].items():
            self.pairs: list[AlignedToken] = []
            # limit type checker complaint to this one line
            versedata: VerseData = vd
            self.target_alignments[bcv] = {
                target: source
                for rec in versedata.records
                for target in rec.target_selectors
                for source in rec.source_selectors
            }
            self.aligned_sources[bcv] = set(self.target_alignments[bcv].values())
            # now build the mapping for this verse
            # but what to do with unaligned sources? somehow need to
            # get them in sequence, even if no target
            for target in versedata.targets:
                if target.id in self.target_alignments[bcv]:
                    sourcetoken = self.mgr.sourceitems[self.target_alignments[bcv][target.id]]
                    altoken = AlignedToken(
                        sourcetoken=sourcetoken, targettoken=target, aligned=True
                    )
                    self.pairs.append(altoken)
                # add unaligned targets and sources
                else:
                    self.pairs.append(AlignedToken(targettoken=target))
            for source in versedata.sources:
                if source.id not in self.aligned_sources[bcv]:
                    self.pairs.append(AlignedToken(sourcetoken=source))
            # could sort here by target ID: but not sure how to get
            # source tokens in a reasonable order
            self.data[bcv] = sorted(self.pairs)


class Writer:
    """Write reverse interlinear data."""

    fieldnames: list[str] = [
        "targetid",
        "targettext",
        "source_verse",
        "skip_space_after",
        "exclude",
        "sourceid",
        "sourcetext",
        "altId",
        "strongs",
        "gloss",
        "gloss2",
        "lemma",
        "pos",
        "morph",
        "required",
    ]

    def __init__(self, reader: Reader) -> None:
        """Initialize an instance given a Reader."""
        self.reader = reader

    def write(self, outpath: Path) -> None:
        """Write the reverse interlinear data to outpath."""
        # create the directory if it doesn't exist
        outpath.parent.mkdir(parents=True, exist_ok=True)
        with outpath.open("w", encoding="utf-8") as outf:
            writer = DictWriter(
                outf, delimiter="\t", fieldnames=self.fieldnames, extrasaction="raise"
            )
            writer.writeheader()
            # write the data
            for bcv, tokenlist in self.reader.items():
                for alignedtoken in tokenlist:
                    writer.writerow(alignedtoken.asdict())
