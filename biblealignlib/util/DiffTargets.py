"""Compare target token sequences between two Manager instances.

Both managers must share the same sourceid and targetlanguage but may
have different targetids (different translations) or alternateids.

For each source verse, uses difflib.SequenceMatcher to produce an
optimal alignment between the two target token sequences. Differences
are stored as DiffRecord instances in a dict keyed by BCV.

>>> from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, target
>>> from biblealignlib.util import DiffTargets
>>> targetlang, sourceid = ("eng", "SBLGNT")
>>> alset1 = AlignmentSet(targetlanguage=targetlang,
        targetid="NIV84",
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
>>> mgr84 = Manager(alset1)
>>> dt84 = DiffTargets.DiffTargets84(mgr84, niv11targets)
>>> len(dt84)
2565

>>> alset2 = AlignmentSet(targetlanguage=targetlang,
        targetid="NIV11",
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
>>> mgr1, mgr2 = Manager(alset1), Manager(alset2)
>>> dt = DiffTargets.DiffTargets(mgr1, mgr2)
>>> len(dt.diffs)                   # number of verses with target differences
>>> dt.diffs["41004003"].data       # SequenceMatcher opcodes for Mark 4:3

"""

from __future__ import annotations

from collections import UserDict
import copy
from dataclasses import dataclass
import difflib
from itertools import zip_longest
from pathlib import Path
from typing import Optional, TextIO, TYPE_CHECKING

from biblealignlib.burrito import (
    AlignmentGroup,
    AlignmentRecord,
    AlignmentReference,
    AlignmentSet,
    BaseToken,
    DiffReason,
    DiffRecord,
    Document,
    Manager,
    Metadata,
    Target,
    TargetReader,
)
from ..burrito.alignments import write_alignment_group
from ..burrito.util import groupby_bcv

if TYPE_CHECKING:
    from ..burrito.manager import Manager
    from ..burrito.VerseData import VerseData

# map single NIV11 tokens to their NIV84 equivalents unconditionally,
# so that SequenceMatcher treats them as equal
# collect these via
#
EQUIVALENT84: dict[str, str] = {
    # maybe there's a VV -> VHV rule here for names? not sure about the full context though
    "Abihud": "Abiud",
    "Elihud": "Eliud",
    "Messiah": "Christ",
    # U+02BC to U+2019 because NIV11 distinguishes: not this
    # happens as a single token though
    "ʼ": "’",
    "baptize": "baptise",
    "fullfill": "fulfil",
    "rooster": "cock",
    "wilderness": "desert",
}

# these are conditioned on a specific verse
BCVEQUIVALENT84: dict[str, dict[str, str]] = {
    "40009007": {"Then": "And"},
    "40014024": {"and": "but"},
    "41005023": {"He": "and"},
    "41016012": {"Afterward": "Afterwards"},
    "42005002": {"He": "he"},
    "42017009": {"Will": "Would"},
    "42017023": {"People": "Men"},
    "42021026": {"People": "Men"},
    "43008001": {"but": "But"},
    "43009017": {"Then": "Finally"},
    "43014024": {"Anyone": "He"},
    "43019018": {"There": "Here"},
    "43020011": {"Now": "but"},
    "46001028": {"God": "He"},
    "46016010": {"When": "If"},
    "47005001": {"For": "Now"},
    "48001021": {"Then": "Later"},
    "52005022": {"reject": "Avoid"},
    "55001009": {"He": "who"},
    "58006016": {"People": "Men"},
    "60003004": {"Rather": "Instead"},
    "65001021": {"keep": "Keep"},
    # # this may be context-dependent
    # "Messiah": "Christ",
    # # context-dependent?
    # "fit": "worthy",
    # "fulfill": "fulfil",
    # "wilderness": "desert",
}


@dataclass
class Operation:
    """Represents a single diff operation between two token sequences."""

    opcode: str
    start1: int
    end1: int
    start2: int
    end2: int

    def __post_init__(self) -> None:
        if self.opcode not in {"equal", "replace", "insert", "delete"}:
            raise ValueError(f"Invalid opcode: {self.opcode}")

    def __repr__(self) -> str:
        return f"Operation({self.opcode!r}, {self.start1}-{self.end1}, {self.start2}-{self.end2})"

    @property
    def length1(self) -> int:
        return self.end1 - self.start1

    @property
    def length2(self) -> int:
        return self.end2 - self.start2

    @property
    def same_length(self) -> bool:
        return self.length1 == self.length2

    @property
    def equal(self) -> bool:
        return self.opcode == "equal"

    @property
    def single_replace(self) -> bool:
        return self.opcode == "replace" and self.length1 == 1 and self.length2 == 1

    @property
    def dual_replace(self) -> bool:
        return self.opcode == "replace" and 4 >= (self.length1 + self.length2) > 2

    def get_tokens(self, tokens: list[BaseToken], sequenceid: str) -> list[BaseToken]:
        """Return the tokens involved in this operation from a sequence."""
        assert sequenceid in ("1", "2"), f"Invalid sequenceid: {sequenceid}"
        if sequenceid == "1":
            return tokens[self.start1 : self.end1]
        else:
            return tokens[self.start2 : self.end2]


def _canonical(text: str) -> str:
    """Return a stable canonical form for EQUIVALENT84 text pairs.

    Both members of a EQUIVALENT84 pair map to the same string (the
    lexicographically smaller of the two), so SequenceMatcher treats
    them as equal. Texts not in EQUIVALENT84 are returned unchanged.
    """
    # about 150 cases of possesseives with weird apostrophe: convert by rule
    if chr(700) in text:
        return text.replace(chr(700), chr(8217))
    else:
        return EQUIVALENT84.get(text, text)


# this doesn't seem as smart about finding subsequences as difflib
# def diff_tokens(
#     seq1: list[BaseToken],
#     seq2: list[BaseToken],
#     idfun: Callable = lambda token: token.id + token.text,
# ) -> list[tuple[int, list[BaseToken]]]:
#     dmp = diff_match_patch()
#     # Map each unique token to a unique character
#     chars1, chars2, token_array = tokens_to_chars(seq1, seq2, idfun)
#     # Compute diff on compact char strings
#     diffs = dmp.diff_main(chars1, chars2)
#     dmp.diff_cleanupEfficiency(diffs)
#     # Expand back to token IDs
#     expanded = []
#     for op, text in diffs:
#         tokens = [token_array[ord(c)] for c in text]
#         #        expanded.append((op, " ".join([tok.id for tok in tokens])))
#         expanded.append((op, tokens))
#     return expanded


def diff_verse_targets(
    bcv: str, targets1: list[Target], targets2: list[Target], bcvequivalents: dict[str, str] = {}
) -> Optional[DiffRecord]:
    """Return a DiffRecord if the target sequences differ, else None.

    Items from targets2 are canonicalized.
    Compares the text of the targets from each alignment set.
    Missing targets are treated as an empty sequence.
    The data attribute of the returned DiffRecord contains the
    SequenceMatcher opcodes as a tuple of (tag, i1, i2, j1, j2)
    5-tuples, where tag is one of 'equal', 'replace', 'insert',
    or 'delete'.
    """
    norm1 = [t.text for t in targets1]
    norm2 = [_canonical(t.text) for t in targets2]
    # do any verse-specific replacements for NIV11 targets
    if bcvequivalents:
        norm2 = [bcvequivalents.get(t.text, t.text) for t in targets2]
    if norm1 == norm2:
        return None
    matcher = difflib.SequenceMatcher(None, norm1, norm2)
    return DiffRecord(
        bcvid=bcv,
        targets1=tuple(targets1),
        targets2=tuple(targets2),
        diffreason=DiffReason.DIFFTARGETS,
        data=tuple(Operation(*op) for op in matcher.get_opcodes()),
    )


# could try here to find alignment records that are a subset of an
# equal region, and then map the token IDs?
# then write out revised records and patch onto the alignment data??


# this still doesn't handle multi-term direct replacements: for those we need to ensure semantic compatability
class DiffTargets84(UserDict):
    missing84: set[str] = {"42023018", "47013014", "64001015"}
    _DIFFLABELS: dict[str, str] = {
        "equal": "=",
        "delete": "-",
        "insert": "+",
        "replace": "~",
        "diff": "<>",
    }
    # some NIV11 verses are numbered differently in NIV84, so we need
    # to map them to the same key for comparison. Note these are not
    # necessarily the same token text! Just an equivalent renumbering
    # based on verse boundaries. This includes some things that won't
    # have alignments, but that's okay.
    # bcvrenumbered11: dict[str, str] = {"64001015": "64001014"}
    niv84_niv11_map: dict[str, str] = {
        "41007021021": "41007022001",
        "41007021022": "41007022002",
        #
        "42018032022": "42018033001",
        "42018032023": "42018033002",
        "42018032024": "42018033003",
        "42018032025": "42018033004",
        "42018032026": "42018033005",
        "42018032027": "42018033006",
        #
        "42020025001": "42020024016",
        "42020025002": "42020024017",
        "42020025003": "42020024018",
        "42020025004": "42020024019",
        "42020025005": "42020024020",
        "42020025006": "42020024021",
        "42020025007": "42020024022",
        #
        "62002013035": "62002014001",
        "62002013036": "62002014002",
        "62002013037": "62002014003",
        "62002013038": "62002014004",
        "62002013039": "62002014005",
        "62002013040": "62002014006",
        "62002013041": "62002014007",
        "62002013042": "62002014008",
        "62002013043": "62002014009",
        "62002013044": "62002014010",
        "62002013045": "62002014011",
        "62002013046": "62002014012",
        "62002013047": "62002014013",
        "62002013048": "62002014014",
        "62002013049": "62002014015",
        #
        "64001014016": "64001015001",
        "64001014017": "64001015002",
        "64001014018": "64001015003",
        "64001014019": "64001015004",
        "64001014020": "64001015005",
        "64001014021": "64001015006",
        "64001014022": "64001015007",
        "64001014023": "64001015008",
        "64001014024": "64001015009",
        "64001014025": "64001015010",
        "64001014026": "64001015011",
        "64001014027": "64001015012",
        "64001014028": "64001015013",
        "64001014029": "64001015014",
        "64001014030": "64001015015",
        "64001014031": "64001015016",
        "64001014032": "64001015017",
        "64001014033": "64001015018",
    }
    # hacky way to avoid outputing the same alignment record more than once
    output_alrecs: dict[str, AlignmentRecord] = {}

    def __init__(
        self,
        mgr84: Manager,
        targets11: TargetReader,
        bcvequivalents: dict[str, dict[str, str]] = {},
    ) -> None:
        super().__init__()
        self.mgr84 = mgr84
        self.niv84bcvtargets: dict[str, list[Target]] = mgr84.bcv["targets"]
        self.targets11: dict[str, Target] = targets11
        self.bcvequivalents = bcvequivalents
        # not correct for versification differences??
        self.niv11bcvtargets: dict[str, list[Target]] = groupby_bcv(self.targets11.values())
        for bcv in self.niv11bcvtargets:
            if bcv not in self.missing84:
                trg84: list[Target] = self.niv84bcvtargets.get(bcv, [])
                trg11: list[Target] = self.niv11bcvtargets[bcv]
                equivalents: dict[str, str] = (
                    self.bcvequivalents.get(bcv, {}) if self.bcvequivalents else {}
                )
                record = diff_verse_targets(bcv, trg84, trg11, equivalents)
                # record.data is like (('equal', 0, 5, 0, 5), ('replace', 5, 6, 5, 6), ('equal', 6, 34, 6, 34), ('replace', 34, 35, 34, 35), ('equal', 35, 38, 35, 38))
                #                if record is not None:
                if record and not self._replaceonly_same_length(record):
                    # then record as a difference
                    self.data[bcv] = record
        # items that are only replacements
        # self.replaceonly: dict[str, DiffRecord] = {
        #     bcv: drec
        #     for bcv, drec in self.items()
        #     if all([(op.opcode in ("equal", "replace")) for op in drec.data])
        # }
        # self.single_replaceonly: dict[str, list[Operation]] = {
        #     bcv: oplist
        #     for bcv, drec in self.replaceonly.items()
        #     if (oplist := [op for op in drec.data if op.single_replace])
        #     if oplist
        # }
        # self.dual_replaceonly: dict[str, list[Operation]] = {
        #     bcv: oplist
        #     for bcv, drec in self.replaceonly.items()
        #     if (oplist := [op for op in drec.data if op.dual_replace])
        #     if oplist
        # }
        self.replaceonly_same_length: dict[str, DiffRecord] = {
            bcv: drec
            for bcv, drec in self.items()
            if all((op.opcode in ("equal", "replace")) for op in drec.data)
            if all(op.same_length for op in drec.data)
        }

    def _replaceonly_same_length(self, diffrec: DiffRecord) -> bool:
        """True if all operations are 'equal' or 'replace' of same length.

        That means token IDs don't need to change in NIV11.
        """
        return all((op.opcode in ("equal", "replace")) and op.same_length for op in diffrec.data)

    def _get_bcv_texts(self, bcv: str) -> tuple[list[str], list[str]]:
        record = self.data.get(bcv)
        if record is None:
            print(f"{bcv}: No differences")
            return [], []
        text84 = [trg.text for trg in self.niv84bcvtargets[bcv]]
        text11 = [trg.text for trg in self.niv11bcvtargets[bcv]]
        return text84, text11

    # def get_single_token_replacements(self) -> dict[str, dict[str, str]]:
    #     # bcv-specific single token replacements
    #     return {bcv: self.replace_single_text(bcv) for bcv, ops in self.single_replaceonly.items()}

    def display_pair_text(self, bcv: str) -> None:
        text84, text11 = self._get_bcv_texts(bcv)
        for pair in zip_longest(text84, text11):
            print(pair)

    # only for single-token replace operations
    def replace_single_text(self, bcv: str) -> dict[str, str]:
        record = self.data.get(bcv)
        text84, text11 = self._get_bcv_texts(bcv)
        replacements: dict[str, str] = {}
        for op in record.data:
            if op.single_replace:
                k = text11[op.start2 : op.end2][0]
                replacements[k] = text84[op.start1 : op.end1][0]
        return replacements

    # replacements where one or both sides have two tokens
    # could consolidate this with replace_single_text
    def replace_dual_text(self, bcv: str) -> dict[str, str]:
        record = self.data.get(bcv)
        text84, text11 = self._get_bcv_texts(bcv)
        replacements: dict[str, str] = {}
        for op in record.data:
            if op.dual_replace:
                k = tuple(text11[op.start2 : op.end2])
                replacements[k] = tuple(text84[op.start1 : op.end1])
        return replacements

    def mismatched_verses(self) -> dict[str, AlignmentRecord]:
        """Some alignment records have a source in one verse and a target in another."""
        return {
            bcv: alrec
            # for bcv in self.niv84bcvtargets
            for bcv in self.mgr84.bcv["versedata"]
            if (versedata := self.mgr84.bcv["versedata"][bcv])
            for alrec in versedata.records
            for source_selector in alrec.source_selectors
            for target_selector in alrec.target_selectors
            if source_selector[:8] != target_selector[:8]
        }

    def _bcvid_span(self, bcvid: str) -> tuple[str, ...]:
        """Expand the BCVID to preceding and following verses, if they exist."""
        previous: str = bcvid[:-3] + f"{int(bcvid[-3:])-1:03}"
        next: str = bcvid[:-3] + f"{int(bcvid[-3:])+1:03}"
        # one special case of cross-chapter alignment for Rev 12:18/13:1
        if next == "66012019":
            next = "66013001"
        return (previous, bcvid, next)

    def _niv11map(self, bcvid: str) -> dict[str, str]:
        """Return a mapping from BCVIDS to token strings for a BCVID.

        Includes adjacent verses.
        """
        # expand to adjacent verses to deal with occasional cross-verse alignments
        # map from SBLGNT to NIV verses when relevant
        return {
            trg.id: trg.tokenstr
            for bcvid in self._bcvid_span(bcvid)
            for trg in self.niv11bcvtargets.get(bcvid, [])
        }

    def _rec11list(self, alrec: AlignmentRecord, niv11map: dict[str, str]) -> list[str]:
        """Return a mapping from NIV11 BCVIDs to token strings from NIV11.

        Maps some NIV84 sub-verse BCVIDs to NIV11 BCVIDs when relevant.
        """
        # get the BCVIDs from alrec.target_selectors: retrieve the id+text from NIV11
        return [
            niv11map[mapped_sel]
            for sel in alrec.target_selectors
            # convert some NIV84 sub-verse BCVIDs to NIV11
            if (mapped_sel := self.niv84_niv11_map.get(sel, sel))
        ]

    def display_diff(self, record: DiffRecord) -> None:
        """Display the differences in a DiffRecord as a readable table.

        One row per token from the longer side of each operation, with a
        symbol indicating the operation: '=' equal, '-' delete, '+' insert,
        '~' replace.
        """
        t1 = record.targets1
        t2 = record.targets2
        col = max(
            (len(t.tokenstr) for t in (*t1, *t2) if t.text),
            default=20,
        )
        # col = max(col, 20)
        header = f"{'Op':2}  {'NIV84':<{col}}  {'NIV11':<{col}}"
        print(f"BCV: {record.bcvid}")
        print(header)
        print("-" * len(header))
        for op in record.data:
            seq1 = [t.tokenstr for t in t1[op.start1 : op.end1]]
            seq2 = [t.tokenstr for t in t2[op.start2 : op.end2]]
            label = self._DIFFLABELS[op.opcode]
            for w1, w2 in zip_longest(seq1, seq2, fillvalue=""):
                print(f"{label:2}  {w1:<{col}}  {w2:<{col}}")

    def _output_matched_bcv(self, outstr: TextIO, versedata: VerseData) -> None:
        """True if both texts are the same or equivalent."""
        niv11map: dict[str, str] = self._niv11map(versedata.bcvid)
        for alrec in versedata.records:
            # rectsv = versedata.record_as_tsv(alrec)
            # get the BCVIDs from alrec.target_selectors: retrieve the id+text from NIV11
            try:
                rec11list: list[str] = self._rec11list(alrec, niv11map)
                rec11 = ", ".join(rec11list)
                # this is outputting NIV11 based on token ID, not matching
                outstr.write(
                    self._DIFFLABELS["equal"]
                    + "\t"
                    + versedata.record_as_tsv(alrec)
                    + "\t"
                    + rec11
                    + "\n"
                )
                self.output_alrecs[alrec.meta.id] = True
            except KeyError as e:
                # Selectors: ['42001025012']
                # niv11map keys: dict_keys(['42001024001', '42001024002', '42001024003', '42001024004', '42001024005', '42001024006', '42001024007', '42001024008', '42001024009', '42001024010', '42001024011', '42001024012', '42001024013', '42001024014', '42001024015'])

                print(f"--- {versedata.bcvid}, KeyError on {e}")
                print(f"Record: {alrec}")

    def _output_diff_operation(
        self, outstr: TextIO, versedata: VerseData, alrec: AlignmentRecord
    ) -> None:
        pass

    def _get_record_target_tokens(
        self, record: AlignmentRecord, tokens: list[BaseToken]
    ) -> list[BaseToken]:
        """Get the target tokens for an AlignmentRecord."""
        # map token IDs to instances
        tokenidmap = {tok.id: tok for tok in tokens}
        return [tokenidmap[sel] for sel in record.target_selectors if sel in tokenidmap]

    def _output_equal_operation(
        self, outstr: TextIO, op: Operation, diffrec: DiffRecord, versedata: VerseData
    ) -> None:
        op_tokens = op.get_tokens(list(diffrec.targets1), "1")
        for alrec in versedata.records:
            if alrec.meta.id in self.output_alrecs:
                return
            # otherwise
            rec_targets: list[BaseToken] = self._get_record_target_tokens(alrec, op_tokens)
            if rec_targets:
                # need mapping here??
                targets_string: str = ", ".join(versedata.tokenstrings(alrec, "targets"))
                outstr.write(
                    self._DIFFLABELS["equal"]
                    + "\t"
                    + versedata.record_as_tsv(alrec)
                    + "\t"
                    + targets_string
                    + "\n"
                )
                self.output_alrecs[alrec.meta.id] = True

    def _output_inequal_operation(
        self, outstr: TextIO, op: Operation, diffrec: DiffRecord, versedata: VerseData
    ) -> None:
        op_tokens1 = op.get_tokens(list(diffrec.targets1), "1")
        op_tokens2 = op.get_tokens(list(diffrec.targets2), "2")
        for alrec in versedata.records:
            if alrec.meta.id in self.output_alrecs:
                return
            # otherwise
            rec_targets: list[BaseToken] = self._get_record_target_tokens(alrec, op_tokens1)
            if rec_targets:
                # need _all_ the NIV11 tokens in the scope of the
                # operation, not just those from the alignment record
                # targets11: list[BaseToken] = self._get_record_target_tokens(alrec, op_tokens2)
                targets11: list[BaseToken] = op_tokens2
                targets11_string: str = ", ".join(t.tokenstr for t in targets11)
                outstr.write(
                    self._DIFFLABELS["diff"]
                    + "\t"
                    + versedata.record_as_tsv(alrec)
                    + "\t\t"
                    + targets11_string
                    + "\n"
                )
                self.output_alrecs[alrec.meta.id] = True

    def write_tsv(self, outpath: Path = None) -> None:
        """Write TSV for review and manual correction."""
        if not outpath:
            outdir = self.mgr84.alignmentset.langdatapath / "NIV84-NIV11"
            outdir.mkdir(parents=True, exist_ok=True)
            outpath = outdir / "NIV84-NIV11-alignments.tsv"
        with outpath.open("w", encoding="utf-8") as f:
            f.write("Label\tAlignmentID\tSBLGNT\tNIV84\tNIV11\tNIV11 unaligned\n")
            for bcv, versedata in self.mgr84.bcv["versedata"].items():
                # this bcv comes from the source numbering: it doesn't
                # always match the targets
                diffrec = self.data.get(bcv)
                if diffrec is None:
                    # no diff between NIV84 and NIV11, so we can just output the NIV84 verse text
                    self._output_matched_bcv(f, self.mgr84.bcv["versedata"][bcv])
                else:
                    # this iteration leaves the alrec's out of order :-<
                    for op in diffrec.data:
                        if op.opcode == "equal":
                            self._output_equal_operation(f, op, diffrec, versedata)
                        else:
                            self._output_inequal_operation(f, op, diffrec, versedata)

                            # the same/equivalent in both versions, so output with mapping
                            # for each alrec within the span of the operation, output it

                        # if op.code == "replace":
                        #     # what is alignment records cross operation boundaries?!?
                        #     base = versedata.record_as_tsv(record)
                        #     niv11replace


class Serialize:
    """Serialize confident alignments for ClearAligner.

    Also outputs difference records and difference information on
    tokens as a checklist of things to review.

    """

    def __init__(self, dt84: DiffTargets84) -> None:
        self.dt84 = dt84
        self.mgr84 = dt84.mgr84
        self.niv84bcvtargets = dt84.niv84bcvtargets
        self.niv11bcvtargets = dt84.niv11bcvtargets
        # new Document for AlignmentRecord instances
        self.niv11_document: Document = Document(docid="NIV11", scheme="BCVW")
        # construct a new manager, with mappings to NIV11
        self.niv11alset: AlignmentSet = AlignmentSet(
            targetlanguage=self.mgr84.alignmentset.targetlanguage,
            targetid="NIV11",
            sourceid=self.mgr84.alignmentset.sourceid,
            langdatapath=self.mgr84.alignmentset.langdatapath,
        )
        # read the existing alignments but then replace the alignment records
        self.mgr11: Manager = Manager(self.niv11alset)
        self.mgr11.targetitems: TargetReader = self.dt84.targets11
        self.niv11_algroup: AlignmentGroup = self.niv11_alignment_group()
        self.mgr11.bcv["records"] = groupby_bcv(
            list(self.niv11_algroup.records), lambda r: r.source_bcv
        )
        # and make VerseData instances for alignments
        versedata: dict[str, VerseData] = {}
        for bcvid in self.mgr11.bcv["records"]:
            try:
                vd: VerseData = self.mgr11.make_versedata(bcvid)
                versedata[bcvid] = vd
            except KeyError:
                print(f"Warning: no records for {bcvid} in NIV11; skipping verse")
        self.mgr11.bcv["versedata"] = versedata

    def _niv84_to_niv11(self, bcv: str) -> dict[str, list[Target]]:
        """Map NIV84 token IDs to NIV11 Target tokens for a verse.

        When a DiffRecord exists for the verse, uses its Operation opcodes:
          equal   → one-to-one positional match
          replace → each NIV84 token maps to all NIV11 tokens in the span
          delete  → NIV84 token maps to nothing (key absent from result)
          insert  → NIV11 token has no NIV84 counterpart (not in result;
                    will appear in the unmatched dump at end of verse)
        When no diff exists the two sequences have identical text and are
        zipped positionally.
        """
        niv84_tokens = self.niv84bcvtargets.get(bcv, [])
        niv11_tokens = self.niv11bcvtargets.get(bcv, [])
        result: dict[str, list[Target]] = {}
        diffrec = self.dt84.data.get(bcv)
        if diffrec is None:
            for t84, t11 in zip(niv84_tokens, niv11_tokens):
                result[t84.id] = [t11]
        else:
            for op in diffrec.data:
                seq84 = niv84_tokens[op.start1 : op.end1]
                seq11 = niv11_tokens[op.start2 : op.end2]
                if op.opcode == "equal":
                    for t84, t11 in zip(seq84, seq11):
                        result[t84.id] = [t11]
                elif op.opcode == "replace":
                    for t84 in seq84:
                        result[t84.id] = list(seq11)
                # delete → key omitted; insert → no NIV84 token, omitted from map
        return result

    # if the target IDs are the same, even if the NIV11 tokens are
    # different, we can still use the NIV84 alignment records
    # but xverse mapping is needed
    def _alrecs_to_niv11(self, bcv: str) -> list[AlignmentRecord]:
        """Return the alignment records from NIV84, mapped to NIV11 targets.

        Only when there aren't significant differences.
        """
        niv84_tokens = self.niv84bcvtargets.get(bcv, [])
        # niv11_tokens = self.niv11bcvtargets.get(bcv, [])
        alrecs_niv84: list[AlignmentRecord] = self.mgr84.bcv["records"][bcv]
        # niv84_to_niv11 = self._niv84_to_niv11(bcv)
        # this only works because each token is equal or equivalent
        #
        # this handles any cases of cross-verse boundary changes
        niv84_niv11_xverse_map: dict[str, str] = {
            t84.id: self.dt84.niv84_niv11_map.get(t84.id, t84.id) for t84 in niv84_tokens
        }
        # in theory, the xverse  map shouldn't interact with the diff-based map ...
        new_alrecs: list[AlignmentRecord] = []
        for alrec in alrecs_niv84:
            niv11_selectors: list[str] = [
                xverse_sel
                for sel in alrec.target_selectors
                if (xverse_sel := niv84_niv11_xverse_map.get(sel, sel))
                # if (to_niv11 := niv84_to_niv11.get(xverse_sel, xverse_sel))
                # for niv11_tok in to_niv11
            ]
            new_reference: AlignmentReference = AlignmentReference(
                document=self.niv11_document, selectors=niv11_selectors
            )
            newmeta = copy.deepcopy(alrec.meta)
            newmeta.origin = "NIV84_transfer"
            new_alrecs.append(
                AlignmentRecord(
                    meta=alrec.meta,
                    references={
                        "source": alrec.references["source"],
                        "target": new_reference,
                    },
                    type=alrec.type,
                )
            )

        return new_alrecs

    def niv11_alignment_group(self) -> AlignmentGroup:
        """Return an AlignmentGroup for NIV11, with aligned records from NIV84 where possible."""
        niv84_algroup: AlignmentGroup = self.mgr84.alignmentsreader.alignmentgroup
        sblgnt_document: Document = niv84_algroup.documents[0]
        niv11_metadata: Metadata = Metadata(conformsTo="0.3", creator="NIV84-NIV11 transfer")
        niv11_alrecs: list[AlignmentRecord] = [
            alrec
            for bcv in self.mgr84.bcv["records"].keys()
            # only those that map cleanly
            if bcv not in self.dt84
            for alrec in self._alrecs_to_niv11(bcv)
        ]
        niv11_algroup: AlignmentGroup = AlignmentGroup(
            documents=(sblgnt_document, self.niv11_document),
            meta=niv11_metadata,
            records=niv11_alrecs,
            roles=niv84_algroup.roles,
            sourcedocid=niv84_algroup.sourcedocid,
            canon=niv84_algroup.canon,
            _type=niv84_algroup._type,
        )
        return niv11_algroup

    def write_diffs(self, outpath: Path = None) -> None:
        """Write diffs as a checklist for manual alignment."""
        if not outpath:
            outdir = self.mgr84.alignmentset.langdatapath / "NIV84-NIV11"
            outdir.mkdir(parents=True, exist_ok=True)
            outpath = outdir / "NIV84-NIV11-diffs.tsv"
        with outpath.open("w", encoding="utf-8") as f:
            f.write("Verse\tOpCode\tNIV84 Tokens\tNIV11 Tokens\n")
            for bcv, diffrec in self.dt84.data.items():
                niv84_tokens = self.niv84bcvtargets.get(bcv, [])
                niv11_tokens = self.niv11bcvtargets.get(bcv, [])
                for op in diffrec.data:
                    seq84 = niv84_tokens[op.start1 : op.end1]
                    seq11 = niv11_tokens[op.start2 : op.end2]
                    f.write(
                        f"{bcv}\t{op.opcode}\t"
                        f"{' '.join(t.tokenstr for t in seq84)}\t"
                        f"{' '.join(t.tokenstr for t in seq11)}\n"
                    )
