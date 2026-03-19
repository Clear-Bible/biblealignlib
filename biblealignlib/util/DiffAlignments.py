"""Compare two alignment groups record by record.

Both groups must share the same sourceid, targetid, and
targetlanguage. This is most useful for checking minor changes to
ensure you haven't introduced errors.

Comparison ignores meta.id (which is assigned on write) but reports
differences in targets and all other meta fields (status, origin, creator, note).

>>> from biblealignlib.burrito import CLEARROOT, AlignmentSet
>>> from biblealignlib.util.DiffAlignments import DiffAlignments
>>> LANGDATAPATH = CLEARROOT / "alignments-eng/data"
>>> alset1 = AlignmentSet(sourceid="SBLGNT", targetid="BSB",
...                       targetlanguage="eng", langdatapath=LANGDATAPATH,
...                       alternateid="manual")
>>> alset2 = AlignmentSet(sourceid="SBLGNT", targetid="BSB",
...                       targetlanguage="eng", langdatapath=LANGDATAPATH,
...                       alternateid="updated")
>>> da = DiffAlignments(alset1, alset2)
>>> da.show()

"""

from dataclasses import dataclass, field

from ..burrito.AlignmentGroup import AlignmentGroup, AlignmentRecord
from ..burrito.AlignmentSet import AlignmentSet
from ..burrito.alignments import AlignmentsReader

# Meta fields compared between records (id is intentionally excluded)
_COMPARED_META_FIELDS = ("creator", "note", "origin", "status")


def _record_key(rec: AlignmentRecord) -> tuple[str, ...]:
    """Return a stable key for matching records across groups.

    Keyed by sorted source selectors, since records are matched on the
    source side and targets may differ.
    """
    return tuple(sorted(rec.source_selectors))


def _meta_diffs(rec1: AlignmentRecord, rec2: AlignmentRecord) -> dict[str, tuple[str, str]]:
    """Return a dict of differing meta fields (excluding id).

    Keys are field names; values are (val_in_rec1, val_in_rec2).
    """
    diffs: dict[str, tuple[str, str]] = {}
    for field_name in _COMPARED_META_FIELDS:
        v1 = getattr(rec1.meta, field_name, "")
        v2 = getattr(rec2.meta, field_name, "")
        if v1 != v2:
            diffs[field_name] = (str(v1), str(v2))
    return diffs


@dataclass
class RecordDiff:
    """Captures differences between two matched alignment records."""

    source_selectors: tuple[str, ...]
    # non-empty when targets differ
    targets1: list[str] = field(default_factory=list)
    targets2: list[str] = field(default_factory=list)
    # non-empty when meta fields (excluding id) differ
    meta_diffs: dict[str, tuple[str, str]] = field(default_factory=dict)

    @property
    def targets_differ(self) -> bool:
        """True if target selectors differ between the two records."""
        return self.targets1 != self.targets2

    def __repr__(self) -> str:
        src = ", ".join(self.source_selectors)
        parts = [f"<RecordDiff src=[{src}]"]
        if self.targets_differ:
            parts.append(f" targets: {self.targets1} -> {self.targets2}")
        for fname, (v1, v2) in self.meta_diffs.items():
            parts.append(f" {fname}: {v1!r} -> {v2!r}")
        parts.append(">")
        return "".join(parts)


class DiffAlignments:
    """Compare two alignment groups from the same source/target pair.

    Records are matched by their source selectors. Differences in
    target selectors and metadata (excluding id) are reported.
    """

    def __init__(self, alset1: AlignmentSet, alset2: AlignmentSet) -> None:
        """Initialize and compute differences."""
        for attr in ("sourceid", "targetid", "targetlanguage"):
            v1 = getattr(alset1, attr)
            v2 = getattr(alset2, attr)
            if v1 != v2:
                raise ValueError(f"AlignmentSets differ on {attr!r}: {v1!r} vs {v2!r}")
        self.alset1 = alset1
        self.alset2 = alset2
        self.group1: AlignmentGroup = AlignmentsReader(alset1).alignmentgroup
        self.group2: AlignmentGroup = AlignmentsReader(alset2).alignmentgroup

        # index each group's records by source-selector key
        self._recs1: dict[tuple[str, ...], AlignmentRecord] = {
            _record_key(r): r for r in self.group1.records
        }
        self._recs2: dict[tuple[str, ...], AlignmentRecord] = {
            _record_key(r): r for r in self.group2.records
        }

        keys1 = set(self._recs1)
        keys2 = set(self._recs2)

        # records present only in one group
        self.only_in_1: list[AlignmentRecord] = [self._recs1[k] for k in sorted(keys1 - keys2)]
        self.only_in_2: list[AlignmentRecord] = [self._recs2[k] for k in sorted(keys2 - keys1)]

        # records present in both; compare targets and meta
        self.record_diffs: list[RecordDiff] = []
        for key in sorted(keys1 & keys2):
            r1, r2 = self._recs1[key], self._recs2[key]
            t1, t2 = sorted(r1.target_selectors), sorted(r2.target_selectors)
            mdiffs = _meta_diffs(r1, r2)
            if t1 != t2 or mdiffs:
                self.record_diffs.append(
                    RecordDiff(source_selectors=key, targets1=t1, targets2=t2, meta_diffs=mdiffs)
                )

    @property
    def has_diffs(self) -> bool:
        """True if any differences were found."""
        return bool(self.only_in_1 or self.only_in_2 or self.record_diffs)

    def show(self) -> None:
        """Print a human-readable summary of all differences."""
        label1 = self.alset1.identifier
        label2 = self.alset2.identifier
        print(f"Comparing {label1!r} vs {label2!r}")
        print(
            f"  {len(self.group1.records)} records in {label1}, "
            f"{len(self.group2.records)} records in {label2}"
        )
        if not self.has_diffs:
            print("  No differences found.")
            return

        if self.only_in_1:
            print(f"\n  Records only in {label1} ({len(self.only_in_1)}):")
            for rec in self.only_in_1:
                src = ", ".join(rec.source_selectors)
                print(f"    - src=[{src}]  tgt={rec.target_selectors}")

        if self.only_in_2:
            print(f"\n  Records only in {label2} ({len(self.only_in_2)}):")
            for rec in self.only_in_2:
                src = ", ".join(rec.source_selectors)
                print(f"    + src=[{src}]  tgt={rec.target_selectors}")

        if self.record_diffs:
            print(f"\n  Records with differences ({len(self.record_diffs)}):")
            for diff in self.record_diffs:
                src = ", ".join(diff.source_selectors)
                print(f"    src=[{src}]")
                if diff.targets_differ:
                    print(f"      targets: {diff.targets1}")
                    print(f"            -> {diff.targets2}")
                for fname, (v1, v2) in diff.meta_diffs.items():
                    print(f"      {fname}: {v1!r} -> {v2!r}")
