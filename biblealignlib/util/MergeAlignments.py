"""Merge two JSON alignment files for the same source, target language, and target version.

The two files typically represent different origins:
- a "manual" file with human-curated alignments (meta.origin='manual')
- a "partial transfer" file produced by Serialize.collect_partial_records
  (meta.origin='NIV84_partial_transfer')

Conflict resolution (applied per BCV):
1. When records from the two files share source or target selectors (i.e. they
   cover the same tokens), keep the one whose meta.origin is 'manual'.  If both
   or neither carry that origin, mgr1 (file 1) takes priority.
2. Records with origin='NIV84_partial_transfer' that do not overlap with any
   record from file 1 are included in the output.
3. Records discarded from the partial-transfer file are collected in
   MergeAlignments.discarded for inspection.

Usage::

    from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager
    from biblealignlib.util.MergeAlignments import MergeAlignments

    langdatapath = CLEARROOT / "alignments-eng/data"
    mgr_manual = Manager(AlignmentSet(
        sourceid="SBLGNT", targetid="NIV11", targetlanguage="eng",
        langdatapath=langdatapath, alternateid="manual"))
    mgr_partial = Manager(AlignmentSet(
        sourceid="SBLGNT", targetid="NIV11", targetlanguage="eng",
        langdatapath=langdatapath, alternateid="partial"))

    ma = MergeAlignments(mgr_manual, mgr_partial)
    print(f"Merged: {len(ma.merged_records)}, discarded: {len(ma.discarded)}")
    ma.write_merge()
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from ..burrito import AlignmentGroup, AlignmentRecord, Manager, write_alignment_group
from ..burrito.AlignmentGroup import Metadata

if TYPE_CHECKING:
    pass

# sentinel origin values
_MANUAL = "manual"
_PARTIAL = "NIV84_partial_transfer"


class MergeAlignments:
    """Merge two alignment files for the same source/language/target.

    Attributes:
        discarded: AlignmentRecord instances from mgr2 that were dropped
            because they conflicted with records from mgr1 or because a
            higher-priority record already covered their selectors.
        merged_records: the reconciled list of AlignmentRecord instances,
            sorted by source selector.
    """

    def __init__(self, mgr1: Manager, mgr2: Manager) -> None:
        """Initialise and run the merge.

        Parameters
        ----------
        mgr1:
            The primary (higher-priority) manager, typically carrying
            manually curated alignments.
        mgr2:
            The secondary manager, typically produced by automated
            transfer (e.g. Serialize.collect_partial_records).
        """
        for attr in ("sourceid", "targetlanguage", "targetid"):
            v1 = getattr(mgr1.alignmentset, attr)
            v2 = getattr(mgr2.alignmentset, attr)
            if v1 != v2:
                raise ValueError(
                    f"Managers must share the same {attr!r}: {v1!r} != {v2!r}"
                )
        self.mgr1 = mgr1
        self.mgr2 = mgr2
        self.discarded: list[AlignmentRecord] = []
        self.merged_records: list[AlignmentRecord] = self._reassign_ids(
            sorted(self._merge_all())
        )

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reassign_ids(records: list[AlignmentRecord]) -> list[AlignmentRecord]:
        """Return new records with sequential BCV-based IDs, discarding original IDs.

        IDs take the form "{bcv}.{n:02}" (e.g. "41004003.01"), matching the
        convention used by write_alignment_group.  The original meta objects are
        deep-copied so the source managers' records are not mutated.
        """
        result: list[AlignmentRecord] = []
        bcv_counters: dict[str, int] = {}
        for alrec in records:
            bcv = alrec.source_bcv
            bcv_counters[bcv] = bcv_counters.get(bcv, 0) + 1
            new_meta = copy.deepcopy(alrec.meta)
            new_meta.id = f"{bcv}.{bcv_counters[bcv]:02}"
            result.append(
                AlignmentRecord(
                    meta=new_meta,
                    references=alrec.references,
                    type=alrec.type,
                )
            )
        return result

    @staticmethod
    def _selector_sets(records: list[AlignmentRecord]) -> tuple[set[str], set[str]]:
        """Return the union of all source and target selectors across records."""
        sources: set[str] = {sel for r in records for sel in r.source_selectors}
        targets: set[str] = {sel for r in records for sel in r.target_selectors}
        return sources, targets

    @staticmethod
    def _overlaps(
        alrec: AlignmentRecord, sources: set[str], targets: set[str]
    ) -> bool:
        """True if alrec shares any source or target selector with the given sets."""
        return bool(
            set(alrec.source_selectors) & sources
            or set(alrec.target_selectors) & targets
        )

    def _merge_bcv(self, bcv: str) -> list[AlignmentRecord]:
        """Return the merged record list for one BCV.

        Records from mgr1 form the base.  Records from mgr2 are added
        only when they either win a conflict (manual beats non-manual) or
        fill a gap (no selector overlap with the current kept set).
        """
        vd1 = self.mgr1.bcv["versedata"].get(bcv)
        vd2 = self.mgr2.bcv["versedata"].get(bcv)
        records1: list[AlignmentRecord] = list(vd1.records) if vd1 else []
        records2: list[AlignmentRecord] = list(vd2.records) if vd2 else []

        if not records2:
            return records1
        if not records1:
            return records2

        # Working set: start with all records from file 1.
        kept: list[AlignmentRecord] = list(records1)
        src_used, trg_used = self._selector_sets(kept)

        for r2 in records2:
            src2 = set(r2.source_selectors)
            trg2 = set(r2.target_selectors)

            if src2 & src_used or trg2 & trg_used:
                # r2 conflicts with at least one kept record.
                # r2 displaces kept records only if it is manual and every
                # conflicting kept record is not manual.
                conflicting = [
                    r for r in kept
                    if set(r.source_selectors) & src2 or set(r.target_selectors) & trg2
                ]
                if r2.meta.origin == _MANUAL and all(
                    r.meta.origin != _MANUAL for r in conflicting
                ):
                    for r in conflicting:
                        kept.remove(r)
                        src_used -= set(r.source_selectors)
                        trg_used -= set(r.target_selectors)
                        if r.meta.origin == _PARTIAL:
                            self.discarded.append(r)
                    kept.append(r2)
                    src_used |= src2
                    trg_used |= trg2
                else:
                    # mgr1 record(s) win; discard r2 if it is a partial transfer.
                    if r2.meta.origin == _PARTIAL:
                        self.discarded.append(r2)
            else:
                # No overlap: r2 fills a gap — include unconditionally.
                kept.append(r2)
                src_used |= src2
                trg_used |= trg2

        return kept

    def _merge_all(self) -> list[AlignmentRecord]:
        """Iterate every BCV present in either manager and collect merged records."""
        all_bcv: set[str] = set(self.mgr1.bcv["versedata"]) | set(
            self.mgr2.bcv["versedata"]
        )
        merged: list[AlignmentRecord] = []
        for bcv in sorted(all_bcv):
            merged.extend(self._merge_bcv(bcv))
        return merged

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def merge(self) -> AlignmentGroup:
        """Return an AlignmentGroup containing the merged records."""
        base_group: AlignmentGroup = self.mgr1.alignmentsreader.alignmentgroup
        meta = Metadata(
            conformsTo=base_group.meta.conformsTo,
            creator=f"MergeAlignments({self.mgr1.alignmentset.alternateid}"
                    f"+{self.mgr2.alignmentset.alternateid})",
        )
        return AlignmentGroup(
            documents=base_group.documents,
            meta=meta,
            records=self.merged_records,
            roles=base_group.roles,
        )

    def write_merge(self, outpath=None) -> None:
        """Write the merged AlignmentGroup to a JSON file.

        If outpath is not supplied, the file is written alongside the
        mgr1 alignment file, with an alternateid combining both inputs.
        """
        alset1 = self.mgr1.alignmentset
        if outpath is None:
            combined_id = (
                alset1.alternateid + "_" + self.mgr2.alignmentset.alternateid
            )
            outpath = alset1.alignmentpath.with_name(
                f"{alset1.sourceid}-{alset1.targetid}-{combined_id}.json"
            )
        merged_group = self.merge()
        with outpath.open("w", encoding="utf-8") as f:
            write_alignment_group(merged_group, f)
