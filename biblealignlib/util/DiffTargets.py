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
from dataclasses import dataclass, field
import difflib
from itertools import zip_longest
from pathlib import Path
from typing import Callable, Optional, TextIO, TYPE_CHECKING

from diff_match_patch import diff_match_patch
from .tokens_to_chars import tokens_to_chars

from ..burrito.BaseToken import BaseToken
from ..burrito.DiffRecord import DiffReason, DiffRecord
from ..burrito.target import Target
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
    # U+02BC to U+2019 because NIV11 distinguishes: not this
    # happens as a single token though
    "ʼ": "’",
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


# this is a two-pass operation:
# Run with default (empty) bcvequivalents
# Run again supplying get_single_token_replacements() as bcvequivalents
# >>> dt84 = DiffTargets.DiffTargets84(mgr84, niv11targets.BCVEQUIVALENT84)
# >>> len(dt84)
# 3784
# >>> dt84 = DiffTargets.DiffTargets84(mgr84, niv11targets, dt84.get_single_token_replacements())
# >>> len(dt84)
# 2879
# this still doesn't handle multi-term direct replacements: for those we need to ensure semantic compatability
class DiffTargets84(UserDict):
    missing84: set[str] = {"42023018", "47013014", "64001015"}
    # some NIV11 verses are numbered differently in NIV84, so we need
    # to map them to the same key for comparison
    bcvrenumbered11: dict[str, str] = {"64001015": "64001014"}

    def __init__(
        self,
        mgr84: Manager,
        targets11: dict[str, Target],
        bcvequivalents: dict[str, dict[str, str]] = {},
    ) -> None:
        super().__init__()
        self.mgr84 = mgr84
        self.niv84bcvtargets: dict[str, list[Target]] = mgr84.bcv["targets"]
        self.targets11: dict[str, Target] = targets11
        self.bcvequivalents = bcvequivalents
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
                if record is not None:
                    self.data[bcv] = record
        # items that are only replacements
        self.replaceonly: dict[str, DiffRecord] = {
            bcv: drec
            for bcv, drec in self.items()
            if all([(op.opcode in ("equal", "replace")) for op in drec.data])
        }
        self.single_replaceonly: dict[str, list[Operation]] = {
            bcv: oplist
            for bcv, drec in self.replaceonly.items()
            if (oplist := [op for op in drec.data if op.single_replace])
            if oplist
        }
        self.dual_replaceonly: dict[str, list[Operation]] = {
            bcv: oplist
            for bcv, drec in self.replaceonly.items()
            if (oplist := [op for op in drec.data if op.dual_replace])
            if oplist
        }

    def _get_bcv_texts(self, bcv) -> tuple[list[str], list[str]]:
        record = self.data.get(bcv)
        if record is None:
            print(f"{bcv}: No differences")
            return
        text84 = [trg.text for trg in self.niv84bcvtargets[bcv]]
        text11 = [trg.text for trg in self.niv11bcvtargets[bcv]]
        return text84, text11

    def get_single_token_replacements(self) -> dict[str, dict[str, str]]:
        # bcv-specific single token replacements
        return {bcv: self.replace_single_text(bcv) for bcv, ops in self.single_replaceonly.items()}

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
        "Expand the BCVID to"

    def _output_matched_bcv(self, outstr: TextIO, versedata: VerseData) -> None:
        """True if both texts are the same or equivalent."""
        # idtextstrings11 = [trg.tokenstr for trg in self.niv11bcvtargets[versedata.bcvid]]
        # "40001015001" -> '40001015001|Elihud'
        #
        # in a few cases this needs to be expanded to adjacent
        # verses. Maybe always expand it because it won't hurt ir
        # irrelevant?
        niv11map: dict[str, str] = {
            trg.id: trg.tokenstr for trg in self.niv11bcvtargets[versedata.bcvid]
        }
        # {src.bare_id: src for src in self.targets}
        for alrec in versedata.records:
            rectsv = versedata.record_as_tsv(alrec)
            # get the BCVIDs from alrec.target_selectors: retrieve the id+text from NIV11
            try:
                rec11list: list[str] = [niv11map[sel] for sel in alrec.target_selectors]
                rec11 = ", ".join(rec11list)
                outstr.write(versedata.record_as_tsv(alrec) + "\t" + rec11 + "\n")
            except KeyError as e:
                # breaks based on BCV mismatches: niv11map has the wrong bcvids
                # 40027041 '40027042007'
                # 41003007 '41003008014'
                # -----
                # 42001024 '42001025012'
                # Record: <AlignmentRecord: {'source': <SBLGNT: ['42001024016']>, 'target': <NIV84: ['42001025012']>}>
                # Selectors: ['42001025012']
                # niv11map keys: dict_keys(['42001024001', '42001024002', '42001024003', '42001024004', '42001024005', '42001024006', '42001024007', '42001024008', '42001024009', '42001024010', '42001024011', '42001024012', '42001024013', '42001024014', '42001024015'])

                print(f"--- {versedata.bcvid}, KeyError on {e}")
                print(f"Record: {alrec}")
                print(f"Selectors: {alrec.target_selectors}")
                print(f"niv11map keys: {niv11map.keys()}")

    def write_tsv(self, outpath: Path = None) -> None:
        """Write TSV for review and manual correction."""
        if not outpath:
            outdir = self.mgr84.alignmentset.langdatapath / "NIV84-NIV11"
            outdir.mkdir(parents=True, exist_ok=True)
            outpath = outdir / "NIV84-NIV11-alignments.tsv"
        with outpath.open("w", encoding="utf-8") as f:
            f.write("AlignmentID\tSBLGNT\tNIV84\tNIV11\tNIV11 unaligned\n")
            for bcv in self.mgr84.bcv["versedata"]:
                # this bcv comes from the source numbering: it doesn't
                # always match the targets
                record = self.data.get(bcv)
                if record is None:
                    self._output_matched_bcv(f, self.mgr84.bcv["versedata"][bcv])


# class DiffTargets:
#     """Compare target token sequences for two Manager instances.

#     Both managers must share the same sourceid and targetlanguage.
#     For each source verse, uses difflib.SequenceMatcher to produce
#     an optimal alignment between the two sequences of included target
#     tokens. Verses where the sequences differ are stored as DiffRecord
#     instances (diffreason=DIFFTARGETS) with the SequenceMatcher opcodes
#     in the data attribute.
#     """

#     def __init__(self, mgr1: Manager, mgr2: Manager) -> None:
#         """Initialize an instance."""
#         self.mgr1 = mgr1
#         self.mgr2 = mgr2
#         for attr in ("sourceid", "targetlanguage"):
#             mgr1attr = getattr(self.mgr1.alignmentset, attr)
#             mgr2attr = getattr(self.mgr2.alignmentset, attr)
#             if mgr1attr != mgr2attr:
#                 raise ValueError(
#                     f"Managers must have the same {attr!r} attribute, "
#                     f"but {mgr1attr!r} != {mgr2attr!r}"
#                 )
#         self.diffs: dict[str, DiffRecord] = self._compute_diffs()

#     def _compute_diffs(self) -> dict[str, DiffRecord]:
#         """Return a dict of bcv → DiffRecord for verses where target sequences differ."""
#         diffs: dict[str, DiffRecord] = {}
#         # potential issues if mgr2 doesn't have the same verses
#         for bcv in self.mgr1.bcv["targets"]:
#             targets1: list[Target] = self.mgr1.bcv["targets"].get(bcv, [])
#             targets2: list[Target] = self.mgr2.bcv["targets"].get(bcv, [])
#             record = diff_verse_targets(bcv, targets1, targets2)
#             if record is not None:
#                 diffs[bcv] = record
#         return diffs
