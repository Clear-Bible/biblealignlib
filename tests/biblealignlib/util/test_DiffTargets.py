"""Test DiffTargets.py."""

import dataclasses

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, Target
from biblealignlib.burrito.DiffRecord import DiffReason, DiffRecord
from biblealignlib.util.DiffTargets import COMPARABLE, DiffTargets, _canonical, diff_verse_targets

ENGLANGDATAPATH = CLEARROOT / "Alignments/data/eng"


@pytest.fixture(scope="module")
def mgr() -> Manager:
    """Return a Manager instance for SBLGNT-BSB."""
    alset = AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )
    return Manager(alset)


@pytest.fixture(scope="module")
def dt(mgr: Manager) -> DiffTargets:
    """Return a DiffTargets instance comparing a manager with itself."""
    return DiffTargets(mgr, mgr)


@pytest.fixture(scope="module")
def targets(mgr: Manager) -> list[Target]:
    """Real non-excluded target list for Mark 4:3."""
    return list(mgr["41004003"].targets_included)


class TestDiffTargetsInit:
    """Test DiffTargets initialization and validation."""

    def test_init(self, dt: DiffTargets) -> None:
        """DiffTargets initializes with a diffs dict."""
        assert isinstance(dt.diffs, dict)

    def test_mismatched_sourceid(self, mgr: Manager) -> None:
        """ValueError raised when sourceids differ."""

        class FakeMgr:
            class alignmentset:
                sourceid = "WLCM"
                targetlanguage = "eng"

        with pytest.raises(ValueError, match="sourceid"):
            DiffTargets(mgr, FakeMgr())  # type: ignore[arg-type]

    def test_mismatched_targetlanguage(self, mgr: Manager) -> None:
        """ValueError raised when targetlanguages differ."""

        class FakeMgr:
            class alignmentset:
                sourceid = "SBLGNT"
                targetlanguage = "fra"

        with pytest.raises(ValueError, match="targetlanguage"):
            DiffTargets(mgr, FakeMgr())  # type: ignore[arg-type]


class TestDiffTargetsSameManager:
    """Tests using the same manager for both sides (no diffs expected)."""

    def test_same_manager_no_diffs(self, dt: DiffTargets) -> None:
        """Comparing a manager with itself produces no diffs."""
        assert len(dt.diffs) == 0

    def test_diffs_keys_are_bcv_strings(self, dt: DiffTargets) -> None:
        """All keys in diffs are 8-character BCV strings."""
        for key in dt.diffs:
            assert len(key) == 8
            assert key.isdigit()


class TestCanonical:
    """Tests for the _canonical normalization function."""

    def test_comparable_pair_maps_to_same_value(self) -> None:
        """Both members of a COMPARABLE pair normalize to the same string."""
        for k, v in COMPARABLE.items():
            assert _canonical(k) == _canonical(v)

    def test_canonical_is_stable(self) -> None:
        """_canonical called twice on the same text returns the same value."""
        assert _canonical("desert") == _canonical("desert")

    def test_unknown_text_unchanged(self) -> None:
        """Text not in COMPARABLE is returned as-is."""
        assert _canonical("hello") == "hello"

    def test_desert_wilderness_equal(self) -> None:
        """'desert' and 'wilderness' normalize to the same canonical form."""
        assert _canonical("desert") == _canonical("wilderness")

    def test_apostrophe_variants_equal(self) -> None:
        """Unicode and ASCII apostrophe variants normalize to the same form."""
        # Retrieve the actual characters from COMPARABLE rather than hardcoding literals
        apostrophe_key = next(k for k in COMPARABLE if "ʼ" in (k, COMPARABLE[k]))
        apostrophe_val = COMPARABLE[apostrophe_key]
        assert _canonical(apostrophe_key) == _canonical(apostrophe_val)

    def test_comparable_symmetric(self) -> None:
        """COMPARABLE contains both directions for each pair."""
        for k, v in COMPARABLE.items():
            assert COMPARABLE[v] == k


class TestDiffVerse:
    """Tests for the diff_verse_targets function."""

    def test_empty_lists_returns_none(self) -> None:
        """_diff_verse returns None when both target lists are empty."""
        assert diff_verse_targets("41004003", [], []) is None

    def test_same_targets_returns_none(self, targets: list[Target]) -> None:
        """_diff_verse returns None when both sides have identical targets."""
        assert diff_verse_targets("41004003", targets, targets) is None

    def test_targets1_only_returns_diffrecord(self, targets: list[Target]) -> None:
        """_diff_verse returns a DiffRecord when only targets1 is non-empty."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        assert isinstance(record, DiffRecord)

    def test_targets2_only_returns_diffrecord(self, targets: list[Target]) -> None:
        """_diff_verse returns a DiffRecord when only targets2 is non-empty."""
        record = diff_verse_targets("41004003", [], targets)
        assert record is not None
        assert isinstance(record, DiffRecord)

    def test_diffrecord_bcvid(self, targets: list[Target]) -> None:
        """DiffRecord bcvid matches the supplied bcv."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        assert record.bcvid == "41004003"

    def test_diffrecord_reason(self, targets: list[Target]) -> None:
        """DiffRecord diffreason is DIFFTARGETS."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        assert record.diffreason == DiffReason.DIFFTARGETS

    def test_diffrecord_targets1_populated(self, targets: list[Target]) -> None:
        """targets1 in the DiffRecord matches what was passed in."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        assert record.targets1 == tuple(targets)
        assert record.targets2 == ()

    def test_diffrecord_targets2_populated(self, targets: list[Target]) -> None:
        """targets2 in the DiffRecord matches what was passed in."""
        record = diff_verse_targets("41004003", [], targets)
        assert record is not None
        assert record.targets1 == ()
        assert record.targets2 == tuple(targets)

    def test_diffrecord_data_is_tuple_of_opcodes(self, targets: list[Target]) -> None:
        """data contains SequenceMatcher opcodes as a tuple of 5-tuples."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        assert isinstance(record.data, tuple)
        assert len(record.data) > 0
        valid_tags = {"equal", "replace", "insert", "delete"}
        for opcode in record.data:
            tag, i1, i2, j1, j2 = opcode
            assert tag in valid_tags
            assert i1 <= i2
            assert j1 <= j2

    def test_delete_only_when_targets2_empty(self, targets: list[Target]) -> None:
        """When targets2 is empty, all opcodes are 'delete'."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        for tag, *_ in record.data:
            assert tag == "delete"

    def test_insert_only_when_targets1_empty(self, targets: list[Target]) -> None:
        """When targets1 is empty, all opcodes are 'insert'."""
        record = diff_verse_targets("41004003", [], targets)
        assert record is not None
        for tag, *_ in record.data:
            assert tag == "insert"

    def test_comparable_pair_treated_as_equal(self, targets: list[Target]) -> None:
        """Replacing a word with its COMPARABLE equivalent produces no diff."""
        t1 = dataclasses.replace(targets[0], text="desert")
        t2 = dataclasses.replace(targets[0], text="wilderness")
        targets1 = [t1] + targets[1:]
        targets2 = [t2] + targets[1:]
        assert diff_verse_targets("41004003", targets1, targets2) is None

    def test_non_comparable_words_produce_diff(self, targets: list[Target]) -> None:
        """Replacing a word with a non-COMPARABLE word produces a diff."""
        t1 = dataclasses.replace(targets[0], text="hello")
        t2 = dataclasses.replace(targets[0], text="world")
        targets1 = [t1] + targets[1:]
        targets2 = [t2] + targets[1:]
        record = diff_verse_targets("41004003", targets1, targets2)
        assert record is not None
