"""Test code in biblealignlib/util/DiffAlignments.py."""

from unittest.mock import patch, MagicMock

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet
from biblealignlib.burrito.AlignmentGroup import (
    AlignmentGroup,
    AlignmentRecord,
    AlignmentReference,
    Document,
    Metadata,
)
from biblealignlib.burrito.AlignmentType import TranslationType
from biblealignlib.util.DiffAlignments import (
    DiffAlignments,
    RecordDiff,
    _meta_diffs,
    _record_key,
)

ENGLANGDATAPATH = CLEARROOT / "Alignments/data/eng"


# ---------------------------------------------------------------------------
# Helpers for building minimal AlignmentRecord instances
# ---------------------------------------------------------------------------

_SRCDOC = Document(docid="SBLGNT", scheme="BCVWP")
_TGTDOC = Document(docid="BSB", scheme="BCVWP")


def _make_record(
    src_selectors: list[str],
    tgt_selectors: list[str],
    record_id: str = "",
    status: str = "created",
    origin: str = "manual",
    creator: str = "",
    note: str = "",
) -> AlignmentRecord:
    """Build a minimal AlignmentRecord for testing."""
    meta = Metadata(id=record_id, status=status, origin=origin, creator=creator, note=note)
    src_ref = AlignmentReference(document=_SRCDOC, selectors=src_selectors)
    tgt_ref = AlignmentReference(document=_TGTDOC, selectors=tgt_selectors)
    return AlignmentRecord(
        meta=meta,
        references={"source": src_ref, "target": tgt_ref},
        type=TranslationType(),
    )


def _make_group(records: list[AlignmentRecord]) -> AlignmentGroup:
    """Build a minimal AlignmentGroup for testing."""
    meta = Metadata(id="test-group", creator="test")
    return AlignmentGroup(
        documents=(_SRCDOC, _TGTDOC),
        meta=meta,
        records=records,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sblgntbsb() -> AlignmentSet:
    """Return a real AlignmentSet for self-comparison tests."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )


@pytest.fixture(scope="module")
def self_diff(sblgntbsb: AlignmentSet) -> DiffAlignments:
    """Return a DiffAlignments comparing an AlignmentSet against itself."""
    return DiffAlignments(sblgntbsb, sblgntbsb)


# ---------------------------------------------------------------------------
# Unit tests: _record_key
# ---------------------------------------------------------------------------


class TestRecordKey:
    """Test the _record_key helper."""

    def test_single_source(self) -> None:
        """Single source selector is returned as a one-element tuple."""
        rec = _make_record(["41004003001"], ["41004003011"])
        assert _record_key(rec) == ("41004003001",)

    def test_multiple_sources_sorted(self) -> None:
        """Multiple source selectors are sorted in the key."""
        rec = _make_record(["41004003002", "41004003001"], ["41004003011"])
        assert _record_key(rec) == ("41004003001", "41004003002")

    def test_key_ignores_targets(self) -> None:
        """Key depends only on source selectors, not targets."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003001"], ["41004003012"])
        assert _record_key(rec1) == _record_key(rec2)


# ---------------------------------------------------------------------------
# Unit tests: _meta_diffs
# ---------------------------------------------------------------------------


class TestMetaDiffs:
    """Test the _meta_diffs helper."""

    def test_no_diffs(self) -> None:
        """Identical records produce an empty diff dict."""
        r1 = _make_record(["41004003001"], ["41004003011"], status="created", origin="manual")
        r2 = _make_record(["41004003001"], ["41004003011"], status="created", origin="manual")
        assert _meta_diffs(r1, r2) == {}

    def test_status_diff(self) -> None:
        """Different status values are captured."""
        r1 = _make_record(["41004003001"], ["41004003011"], status="created")
        r2 = _make_record(["41004003001"], ["41004003011"], status="approved")
        diffs = _meta_diffs(r1, r2)
        assert "status" in diffs
        assert diffs["status"] == ("created", "approved")

    def test_origin_diff(self) -> None:
        """Different origin values are captured."""
        r1 = _make_record(["41004003001"], ["41004003011"], origin="manual")
        r2 = _make_record(["41004003001"], ["41004003011"], origin="eflomal")
        assert "origin" in _meta_diffs(r1, r2)

    def test_id_ignored(self) -> None:
        """id differences are not reported."""
        r1 = _make_record(["41004003001"], ["41004003011"], record_id="41004003.1")
        r2 = _make_record(["41004003001"], ["41004003011"], record_id="41004003.99")
        assert _meta_diffs(r1, r2) == {}

    def test_multiple_diffs(self) -> None:
        """Multiple differing fields are all reported."""
        r1 = _make_record(["41004003001"], ["41004003011"], status="created", note="")
        r2 = _make_record(["41004003001"], ["41004003011"], status="approved", note="revised")
        diffs = _meta_diffs(r1, r2)
        assert "status" in diffs
        assert "note" in diffs


# ---------------------------------------------------------------------------
# Unit tests: RecordDiff
# ---------------------------------------------------------------------------


class TestRecordDiff:
    """Test the RecordDiff dataclass."""

    def test_targets_differ_true(self) -> None:
        """targets_differ is True when target lists differ."""
        diff = RecordDiff(
            source_selectors=("41004003001",),
            targets1=["41004003011"],
            targets2=["41004003012"],
        )
        assert diff.targets_differ

    def test_targets_differ_false(self) -> None:
        """targets_differ is False when target lists are equal."""
        diff = RecordDiff(
            source_selectors=("41004003001",),
            targets1=["41004003011"],
            targets2=["41004003011"],
        )
        assert not diff.targets_differ

    def test_repr_targets(self) -> None:
        """repr includes target diff when targets differ."""
        diff = RecordDiff(
            source_selectors=("41004003001",),
            targets1=["41004003011"],
            targets2=["41004003012"],
        )
        assert "targets" in repr(diff)
        assert "41004003001" in repr(diff)

    def test_repr_meta(self) -> None:
        """repr includes meta field name and values when meta differs."""
        diff = RecordDiff(
            source_selectors=("41004003001",),
            targets1=["41004003011"],
            targets2=["41004003011"],
            meta_diffs={"status": ("created", "approved")},
        )
        r = repr(diff)
        assert "status" in r
        assert "created" in r
        assert "approved" in r


# ---------------------------------------------------------------------------
# Integration tests: DiffAlignments with a real AlignmentSet
# ---------------------------------------------------------------------------


class TestDiffAlignmentsSelf:
    """DiffAlignments comparing an AlignmentSet against itself."""

    def test_no_diffs(self, self_diff: DiffAlignments) -> None:
        """Self-comparison produces no differences."""
        assert not self_diff.has_diffs

    def test_only_in_1_empty(self, self_diff: DiffAlignments) -> None:
        """No records are only in group 1."""
        assert self_diff.only_in_1 == []

    def test_only_in_2_empty(self, self_diff: DiffAlignments) -> None:
        """No records are only in group 2."""
        assert self_diff.only_in_2 == []

    def test_record_diffs_empty(self, self_diff: DiffAlignments) -> None:
        """No records differ."""
        assert self_diff.record_diffs == []

    def test_show_no_diffs(self, self_diff: DiffAlignments, capsys) -> None:
        """show() reports no differences for a self-comparison."""
        self_diff.show()
        output = capsys.readouterr().out
        assert "No differences found" in output


class TestDiffAlignmentsValidation:
    """DiffAlignments raises ValueError for incompatible AlignmentSets."""

    def test_mismatched_sourceid(self, sblgntbsb: AlignmentSet) -> None:
        """Raises ValueError when sourceids differ."""
        other = MagicMock(spec=AlignmentSet)
        other.sourceid = "BGNT"
        other.targetid = sblgntbsb.targetid
        other.targetlanguage = sblgntbsb.targetlanguage
        with pytest.raises(ValueError, match="sourceid"):
            DiffAlignments(sblgntbsb, other)

    def test_mismatched_targetid(self, sblgntbsb: AlignmentSet) -> None:
        """Raises ValueError when targetids differ."""
        other = MagicMock(spec=AlignmentSet)
        other.sourceid = sblgntbsb.sourceid
        other.targetid = "NIV11"
        other.targetlanguage = sblgntbsb.targetlanguage
        with pytest.raises(ValueError, match="targetid"):
            DiffAlignments(sblgntbsb, other)

    def test_mismatched_targetlanguage(self, sblgntbsb: AlignmentSet) -> None:
        """Raises ValueError when targetlanguages differ."""
        other = MagicMock(spec=AlignmentSet)
        other.sourceid = sblgntbsb.sourceid
        other.targetid = sblgntbsb.targetid
        other.targetlanguage = "hin"
        with pytest.raises(ValueError, match="targetlanguage"):
            DiffAlignments(sblgntbsb, other)


# ---------------------------------------------------------------------------
# Integration tests: DiffAlignments with synthetic groups
# ---------------------------------------------------------------------------


def _make_diff_alignments(
    group1: AlignmentGroup, group2: AlignmentGroup, alset: AlignmentSet
) -> DiffAlignments:
    """Return a DiffAlignments with patched AlignmentsReader output."""
    reader1 = MagicMock()
    reader1.alignmentgroup = group1
    reader2 = MagicMock()
    reader2.alignmentgroup = group2

    with patch(
        "biblealignlib.util.DiffAlignments.AlignmentsReader",
        side_effect=[reader1, reader2],
    ):
        return DiffAlignments(alset, alset)


@pytest.fixture(scope="module")
def sblgntbsb_for_synthetic() -> AlignmentSet:
    """Separate fixture so synthetic tests don't share module scope with self_diff."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )


class TestDiffAlignmentsSynthetic:
    """DiffAlignments behaviour with controlled synthetic data."""

    def test_only_in_1(self, sblgntbsb_for_synthetic: AlignmentSet) -> None:
        """Records present only in group 1 appear in only_in_1."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003002"], ["41004003012"])
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        assert len(da.only_in_1) == 1
        assert da.only_in_1[0].source_selectors == ["41004003001"]

    def test_only_in_2(self, sblgntbsb_for_synthetic: AlignmentSet) -> None:
        """Records present only in group 2 appear in only_in_2."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003002"], ["41004003012"])
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        assert len(da.only_in_2) == 1
        assert da.only_in_2[0].source_selectors == ["41004003002"]

    def test_target_diff_detected(self, sblgntbsb_for_synthetic: AlignmentSet) -> None:
        """A record with changed targets appears in record_diffs."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003001"], ["41004003012"])
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        assert len(da.record_diffs) == 1
        assert da.record_diffs[0].targets_differ

    def test_meta_diff_detected(self, sblgntbsb_for_synthetic: AlignmentSet) -> None:
        """A record with changed status appears in record_diffs."""
        rec1 = _make_record(["41004003001"], ["41004003011"], status="created")
        rec2 = _make_record(["41004003001"], ["41004003011"], status="approved")
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        assert len(da.record_diffs) == 1
        assert "status" in da.record_diffs[0].meta_diffs

    def test_id_diff_not_detected(self, sblgntbsb_for_synthetic: AlignmentSet) -> None:
        """A record differing only in meta.id is not reported as a diff."""
        rec1 = _make_record(["41004003001"], ["41004003011"], record_id="41004003.1")
        rec2 = _make_record(["41004003001"], ["41004003011"], record_id="41004003.99")
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        assert not da.has_diffs

    def test_has_diffs_true(self, sblgntbsb_for_synthetic: AlignmentSet) -> None:
        """has_diffs is True when differences exist."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003001"], ["41004003012"])
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        assert da.has_diffs

    def test_show_includes_source_selectors(
        self, sblgntbsb_for_synthetic: AlignmentSet, capsys
    ) -> None:
        """show() includes the source selector in the output for diffs."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003001"], ["41004003012"])
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        da.show()
        output = capsys.readouterr().out
        assert "41004003001" in output

    def test_show_only_in_1_marker(
        self, sblgntbsb_for_synthetic: AlignmentSet, capsys
    ) -> None:
        """show() marks records only in group 1 with '-'."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003002"], ["41004003012"])
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        da.show()
        output = capsys.readouterr().out
        assert "- src=" in output

    def test_show_only_in_2_marker(
        self, sblgntbsb_for_synthetic: AlignmentSet, capsys
    ) -> None:
        """show() marks records only in group 2 with '+'."""
        rec1 = _make_record(["41004003001"], ["41004003011"])
        rec2 = _make_record(["41004003002"], ["41004003012"])
        group1 = _make_group([rec1])
        group2 = _make_group([rec2])
        da = _make_diff_alignments(group1, group2, sblgntbsb_for_synthetic)
        da.show()
        output = capsys.readouterr().out
        assert "+ src=" in output
