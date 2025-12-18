"""Class for managing alignments and tokens at the verse level.

Given mgr, a Manager instance:

>>> jhn20_20 = mgr["44020020"]
>>> jhn20_20.display()
------------
Source: 44020020002: οὐδὲν		 (nothing, οὐδείς, adj)
Target: 44020020006: না		 ('', False, False)
------------
Source: 44020020003: ὑπεστειλάμην		 (I did shrink back, ὑποστέλλω, verb)
Target: 44020020003: কোনও		 ('', False, False)
Target: 44020020004: কথা		 ('', False, False)
Target: 44020020005: গোপন		 ('', False, False)
------------
Source: 44020020004: τῶν		 (of that, ὁ, det)
Target: 44020020013: মধ্যে		 ('', False, False)
------------
Source: 44020020005: συμφερόντων		 (being profitable, συμφέρω, verb)
Target: 44020020012: সাধারনের		 ('', False, False)
------------
Source: 44020020007: μὴ		 (not, μή, adv)
Source: 44020020008: ἀναγγεῖλαι		 (to declare, ἀναγγέλλω, verb)
Target: 44020020020: দ্বিধাবোধ		 ('', False, False)
Target: 44020020021: করিনি		 ('', False, False)
...

"""

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd


from .BaseToken import BaseToken
from .source import Source
from .target import Target
from .AlignmentGroup import AlignmentRecord


class DiffReason(Enum):
    """Enumerate constants for alignment differences."""

    DIFFLEN = "Different number of alignments"
    DIFFSOURCES = "Source selectors differ"
    DIFFTARGETS = "Target selectors differ"
    DIFFNOTES = "Different notes"
    DIFFSTATUS = "Different status"


@dataclass
class DiffRecord:
    """Container for data on alignment differences.

    The same verse could have multiple alignment differences.
    """

    # the alignment BCV
    bcvid: str
    # the data in the first alignment
    sources1: tuple[Source, ...] = ()
    targets1: tuple[Target, ...] = ()
    # the data in the second alignment
    sources2: tuple[Source, ...] = ()
    targets2: tuple[Target, ...] = ()
    # why it's different
    diffreason: Optional[DiffReason] = None
    # any auxiliary data
    data: tuple = ()

    def __repr__(self) -> str:
        """Return a string representation."""
        basestr = (
            f"<DiffRecord ({self.bcvid}): '{self.diffreason.value if self.diffreason else None}'"
        )
        if self.data:
            basestr += ", " + repr(self.data)
        basestr += ">"
        return basestr


@dataclass
class VerseData:
    """Manage alignments, sources, and targets for a verse.

    Verse references are from the source. In a few cases, that means
    target BCV's won't match!

    """

    # unique identifier for book, chapter, and verse
    bcvid: str
    alignments: list[tuple[list[Source], list[Target]]]
    records: tuple[AlignmentRecord, ...]
    sources: list[Source]
    # includes excluded tokens
    targets: list[Target]
    # computed: omits excluded tokens
    targets_included: tuple[Target, ...] = ()
    _typeattrs = ["sources", "targets"]

    def __post_init__(self) -> None:
        """Compute values after initialization."""
        self.targets_included = tuple([tok for tok in self.targets if not tok.exclude])

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"<VerseData: {self.bcvid}>"

    @property
    def aligned_sources(self) -> list[Source]:
        """Return list of aligned source tokens.

        Note this checks tokens, not alignment records. If a token is
        aligned in one instance but not in another, this will return
        it.

        """
        aligned: set[Source] = {src for srcs, _ in self.alignments for src in srcs}
        return [src for src in self.sources if src in aligned]

    @property
    def unaligned_sources(self) -> list[Source]:
        """Return list of unaligned source tokens.

        Note this checks tokens, not alignment records. If a token is
        aligned in one instance but not in another, this will not
        return it.

        """
        return [src for src in self.sources if src not in self.aligned_sources]

    @property
    def aligned_targets(self) -> list[Source]:
        """Return list of aligned target tokens that are not excluded."""
        aligned: set[Target] = {trg for _, trgs in self.alignments for trg in trgs}
        return [trg for trg in self.targets_included if trg in aligned]

    @property
    def unaligned_targets(self) -> list[Target]:
        """Return list of unaligned target tokens that are not excluded."""
        return [trg for trg in self.targets_included if trg not in self.aligned_targets]

    def get_pairs(self, essential: bool = False) -> list[tuple[Source, Target]]:
        """Return pharaoh-style pairs of source and target tokens.

        Tokens are repeated as necessary in the sequence to express
        multiple alignments.

        With essential=True (default is False), only return pairs
        where the source token has one of [noun, verb, adjective,
        adverb] as part-of-speech.

        """
        pairs: list[tuple[Source, Target]] = []
        if essential:
            pairs = [
                (s, t) for src, trg in self.alignments for s in src if s.is_content for t in trg
            ]
        else:
            pairs = [(s, t) for src, trg in self.alignments for s in src for t in trg]
        return pairs

    def display(self, termsonly: bool = False) -> None:
        """Display the alignments in a readable view."""
        for sources, targets in self.alignments:
            print("------------")
            if termsonly:
                print(f"{list(src.text for src in sources)}-{list(trg.text for trg in targets)}")
            else:
                for src in sources:
                    print(f"Source: {src._display}")
                for trg in targets:
                    print(f"Target: {trg._display}")

    def unaligned(self, typeattr: str = "targets", keepexcluded: bool = False) -> None:
        """Display tokens from typeattr that are _not_ aligned."""
        assert typeattr in self._typeattrs, f"typeattr should be one of {self._typeattrs}"
        tokens: tuple[BaseToken, ...] = getattr(self, typeattr)
        if typeattr == "targets" and not keepexcluded:
            tokens = self.targets_included
        unaligned = self.unaligned_targets if typeattr == "targets" else self.unaligned_sources
        for token in tokens:
            if token in unaligned:
                print(token._display)

    def table(self) -> None:
        """Display a tabbed table of alignments"""
        for sources, targets in self.alignments:
            print(
                " ".join([src.text for src in sources]),
                "\t",
                " ".join([trg.text for trg in targets]),
            )

    def get_texts(
        self, typeattr: str = "targets", unique: bool = False, keepexcluded: bool = False
    ) -> list[str]:
        """Return a list of text attributes for target or source items.

        With unique=True, add a numeric suffix as necessary to make
        each item unique. This means duplicated items will no longer
        be exact matches. The index is the position in the list of
        tokens.

        Drop excluded tokens unless keepexcluded=True (default is
        False).

        """
        assert typeattr in self._typeattrs, f"typeattr should be one of {self._typeattrs}"
        tokens = getattr(self, typeattr)
        if typeattr == "targets" and not keepexcluded:
            tokens = self.targets_included
        if unique:
            cnt: Counter = Counter()
            texts: list[str] = []
            for item in tokens:
                itext = item.text
                if itext in cnt:
                    texts.append(f"{itext}.{cnt[itext]}")
                else:
                    texts.append(itext)
                cnt[itext] = cnt[itext] + 1
        else:
            texts = [item.text for item in tokens]
        return texts

    ## NOT YET WORKING
    # def generate_html_table(self) -> str:
    #     """Generate an HTML table with one row for each source item and one column for each target item."""
    #     table_html = "<table>"
    #     # Add table header row with target item names
    #     table_html += "<tr>"
    #     for target in self.targets:
    #         table_html += f"<th>{target.text}</th>"
    #     table_html += "</tr>"
    #     # Add table rows with source item values
    #     for source in self.sources:
    #         table_html += "<tr>"
    #         for target in self.targets:
    #             # WORKING HERE: Copilot code needs checking
    #             if source in target_sources.get(target, []):
    #                 table_html += "<td>X</td>"
    #             else:
    #                 table_html += "<td></td>"
    #         table_html += "</tr>"
    #     table_html += "</table>"
    #     return table_html

    # no typing hints for pd.Dataframe
    def dataframe(
        self, hitmark: str = "-G-", missmark: str = "   ", srcattr: str = "text"
    ) -> pd.DataFrame:
        """Return a DataFrame showing alignments.

        Target terms for column names, source terms for
        index. Alignments are indicated with the hitmark string:
        otherwise the missmark string is used.

        """

        def get_mark(src: Source, trg: Target) -> str:
            return hitmark if (src in aligned_target_sources.get(trg, {})) else missmark

        # dict mapping each target instance to aligned source instances
        aligned_target_sources = {trg: alpair[0] for alpair in self.alignments for trg in alpair[1]}
        target_text = dict(zip(self.targets_included, self.get_texts(unique=True)))
        # dict mapping
        dfdata = {
            textdisplay: [get_mark(src, trg) for src in self.sources]
            for _ in enumerate(self.alignments)
            for (trg, textdisplay) in target_text.items()
        }
        # add source items as index
        # this either has no effect (outside Jupyter) or raises some obscure error in Jupyter
        # df.style.set_properties(**{"text-align": "center"})
        return pd.DataFrame(dfdata, index=[getattr(src, srcattr) for src in self.sources])

    @staticmethod
    def _diff_pair(
        bcvid: str,
        pair: tuple[tuple[list[Source], list[Target]], tuple[list[Source], list[Target]]],
    ) -> Optional[DiffRecord]:
        """Compare an alignment pair of Source and Target."""
        if pair[0] != pair[1]:
            # assumes the order (source, target)
            sources1, targets1 = pair[0]
            sources2, targets2 = pair[1]
            if sources1 != sources2:
                return DiffRecord(
                    bcvid=bcvid, diffreason=DiffReason.DIFFSOURCES, data=(sources1, sources2)
                )
            if targets1 != targets2:
                return DiffRecord(
                    bcvid=bcvid, diffreason=DiffReason.DIFFTARGETS, data=(targets1, targets2)
                )
        return None

    # TODO: compare
    def diff(self, other: "VerseData") -> Optional[list[DiffRecord]]:
        """Return a (possibly empty) list of differences between the alignments data.

        If there are a different number of alignments, that's the only
        difference reported. Otherwise compaires all the alignments,
        pairwise.

        """
        assert isinstance(other, VerseData), "Can only compare two VerseData instances."
        if len(self.alignments) != len(other.alignments):
            # no point continuing to compare here
            return [DiffRecord(bcvid=self.bcvid, diffreason=DiffReason.DIFFLEN)]
        else:
            # use a list comprehension
            diffs: list[DiffRecord] = []
            for pair in zip(self.alignments, other.alignments):
                result = self._diff_pair(bcvid=self.bcvid, pair=pair)
                if result:
                    diffs.append(result)
            # need to consolidate this better
            for rec1, rec2 in zip(self.records, other.records):
                if rec1.meta.status != rec2.meta.status:
                    diffstatus = DiffRecord(
                        bcvid=self.bcvid,
                        diffreason=DiffReason.DIFFSTATUS,
                        data=(rec1.meta.status, rec2.meta.status),
                    )
                    diffs.append(diffstatus)
                if rec1.meta.note != rec2.meta.note:
                    diffnotes = DiffRecord(
                        bcvid=self.bcvid,
                        diffreason=DiffReason.DIFFNOTES,
                        data=(rec1.meta.note, rec2.meta.note),
                    )
                    diffs.append(diffnotes)
            return diffs
