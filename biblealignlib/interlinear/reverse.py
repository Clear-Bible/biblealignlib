"""Generate integrated data for interlinears/reverse-interlinears (as done for YWAM).

>>> from biblealignlib.burrito import CLEARROOT, Manager, AlignmentSet
>>> from biblealignlib.interlinear.reverse import Reader, Writer
>>> targetlang, targetid, sourceid = ("eng", "BSB", "SBLGNT")
>>> alset = AlignmentSet(targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
>>> mgr = Manager(alset)
>>> rd = Reader(mgr)
# write it out
>>> wr = Writer(rd)
>>> wr.write(CLEARROOT / f"alignments-{targetlang}/data/YWAM_share/NIV11" / f"{sourceid}-{targetid}-aligned.tsv")

"""

from collections import UserDict
from csv import DictWriter
from pathlib import Path

from ..burrito import Manager, Source, Target, VerseData, groupby_bcv

from .token import AlignedToken


# this might should join in the full Macula data, not just what's in
# the alignments. That would provide Louw-Nida numbers, subjref,
# referent, etc.
class Reader(UserDict):
    """Read alignment data for creating reverse interlinear data.

    # keys are BCVs, values are lists of AlignedToken objects, which
    # only cover the aligned data (not the full set of tokens).
    >>> rd["01001001"]
    [<AlignedToken(targetid=01001001001, aligned)>, ...]

    """

    def __init__(self, mgr: Manager, exclude: bool = False) -> None:
        """Initialize an instance.

        With exclude = True (the default), exclude target tokens with exclude=True.
        """
        super().__init__(self)
        self.mgr = mgr
        # RETHINK: just iterate through all the target tokens and
        # build a big list of AlignedTokens
        self.aligned_tokens: list[AlignedToken] = []
        self.target_alignments = self.mgr.get_target_alignments()
        # iterate over all target tokens that aren't excluded (not
        # just aligned ones)
        if exclude:
            included_targets = [t for t in self.mgr.targetitems.values() if not t.exclude]
        else:
            included_targets = list(self.mgr.targetitems.values())
        for target in included_targets:
            if target in self.target_alignments:
                source = self.target_alignments[target]
                aligned_token = AlignedToken(targettoken=target, sourcetoken=source, aligned=True)
                self.aligned_tokens.append(aligned_token)
            else:
                unaligned_token = AlignedToken(targettoken=target)
                self.aligned_tokens.append(unaligned_token)
        self.aligned_tokens.sort()
        # then collect unaligned source tokens
        self.source_alignments = self.mgr.get_source_alignments()
        for source in self.mgr.sourceitems.values():
            if source not in self.source_alignments:
                unaligned_token = AlignedToken(sourcetoken=source)
                self.aligned_tokens.append(unaligned_token)


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
        # should write a manifest here for posterity
        with outpath.open("w", encoding="utf-8") as outf:
            writer = DictWriter(
                outf, delimiter="\t", fieldnames=self.fieldnames, extrasaction="raise"
            )
            writer.writeheader()
            # write the data
            for alignedtoken in self.reader.aligned_tokens:
                writer.writerow(alignedtoken.asdict())
