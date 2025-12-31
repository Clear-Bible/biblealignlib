"""Generate integrated data for interlinears/reverse-interlinears (as done for YWAM).

The output spec for Writer():
- TSV with one row for each target, in target order, with aligned source data where available.
    - If a target is unaligned, it produces one row with empty source data.
    - If a source is aligned with multiple targets, it appears multiple times.
    - If a target is aligned with multiple sources, it produces multiple rows.
    - Is a source is unaligned, it appears close in sequence to the
      target with the same index. This may be imperfect.
- The default is to include all target tokens, even those marked exclude=True (e.g. punctuation).
- The output columns are defined by Writer().fieldnames


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

from collections import UserList
from csv import DictWriter
from pathlib import Path

from ..burrito import Manager, Source, Target

from .token import AlignedToken


# this might should join in the full Macula data, not just what's in
# the alignments. That would provide Louw-Nida numbers, subjref,
# referent, etc.
# this might should join in the full Macula data, not just what's in
# the alignments. That would provide Louw-Nida numbers, subjref,
# referent, etc.
class Reader(UserList):
    """Read alignment data for creating reverse interlinear data.

    Exposes a list of AlignedToken objects via .aligned_tokens.
    """

    def __init__(self, mgr: Manager, exclude: bool = False) -> None:
        """Initialize an instance.

        With exclude = True (the default is False), exclude target tokens with exclude=True.
        """
        super().__init__()
        self.mgr = mgr
        # RETHINK: just iterate through all the target tokens and
        # build a big list of AlignedTokens
        self.aligned_tokens: list[AlignedToken] = []
        self.target_alignments: dict[Target, list[list[Source]]] = self.mgr.get_target_alignments()
        # iterate over all target tokens that aren't excluded (not
        # just aligned ones)
        if exclude:
            self.included_targets = [t for t in self.mgr.targetitems.values() if not t.exclude]
        else:
            self.included_targets = list(self.mgr.targetitems.values())
        for target in self.included_targets:
            if target in self.target_alignments:
                sourceslist = self.target_alignments[target]
                for sources in sourceslist:
                    for source in sources:
                        aligned_token = AlignedToken(
                            targettoken=target, sourcetoken=source, aligned=True
                        )
                        self.aligned_tokens.append(aligned_token)
            else:
                unaligned_token = AlignedToken(targettoken=target)
                self.aligned_tokens.append(unaligned_token)
        self.aligned_tokens.sort()
        # then collect unaligned source tokens
        self.source_alignments: set[Source] = self.mgr.get_source_alignments()
        for source in self.mgr.sourceitems.values():
            if source not in self.source_alignments:
                unaligned_token = AlignedToken(sourcetoken=source)
                self.aligned_tokens.append(unaligned_token)
        # order the whole list
        self.data = sorted(self.aligned_tokens)


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
            for alignedtoken in self.reader:
                writer.writerow(alignedtoken.asdict())
