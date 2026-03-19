"""Test DiffTargets.py."""

import dataclasses
from unittest.mock import MagicMock, PropertyMock

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, Target
from biblealignlib.burrito.DiffRecord import DiffReason, DiffRecord
from biblealignlib.util.DiffTargets import EQUIVALENT84, DiffTargets84, _canonical, diff_verse_targets

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
def targets(mgr: Manager) -> list[Target]:
    """Real non-excluded target list for Mark 4:3."""
    return list(mgr["41004003"].targets_included)


class TestCanonical:
    """Tests for the _canonical normalization function."""

    def test_equivalent84_key_maps_to_value(self) -> None:
        """Keys in EQUIVALENT84 are mapped to their replacement by _canonical."""
        for k, v in EQUIVALENT84.items():
            if chr(700) not in k:
                assert _canonical(k) == v

    def test_canonical_is_stable(self) -> None:
        """_canonical called twice on the same text returns the same value."""
        assert _canonical("desert") == _canonical("desert")

    def test_unknown_text_unchanged(self) -> None:
        """Text not in EQUIVALENT84 is returned as-is."""
        assert _canonical("hello") == "hello"

    def test_apostrophe_chr700_replaced(self) -> None:
        """Text containing chr(700) has it replaced with chr(8217)."""
        text_with_700 = "test" + chr(700) + "s"
        result = _canonical(text_with_700)
        assert chr(700) not in result
        assert chr(8217) in result

    def test_text_without_chr700_not_affected_by_chr700_rule(self) -> None:
        """Text without chr(700) is looked up in EQUIVALENT84, not the chr rule."""
        assert _canonical("Abihud") == "Abiud"


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

    def test_diffrecord_data_is_tuple_of_operations(self, targets: list[Target]) -> None:
        """data contains SequenceMatcher results as a tuple of Operation instances."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        assert isinstance(record.data, tuple)
        assert len(record.data) > 0
        valid_tags = {"equal", "replace", "insert", "delete"}
        for op in record.data:
            assert op.opcode in valid_tags
            assert op.start1 <= op.end1
            assert op.start2 <= op.end2

    def test_delete_only_when_targets2_empty(self, targets: list[Target]) -> None:
        """When targets2 is empty, all opcodes are 'delete'."""
        record = diff_verse_targets("41004003", targets, [])
        assert record is not None
        for op in record.data:
            assert op.opcode == "delete"

    def test_insert_only_when_targets1_empty(self, targets: list[Target]) -> None:
        """When targets1 is empty, all opcodes are 'insert'."""
        record = diff_verse_targets("41004003", [], targets)
        assert record is not None
        for op in record.data:
            assert op.opcode == "insert"

    def test_equivalent84_pair_treated_as_equal(self, targets: list[Target]) -> None:
        """EQUIVALENT84 canonicalization is applied to targets2, not targets1.

        "Abihud" in targets2 maps to "Abiud" via _canonical; if targets1 already
        has "Abiud" (the canonical form), the two sequences compare as equal.
        """
        t1 = dataclasses.replace(targets[0], text="Abiud")   # targets1: raw, no canonicalization
        t2 = dataclasses.replace(targets[0], text="Abihud")  # targets2: "Abihud" -> "Abiud"
        targets1 = [t1] + targets[1:]
        targets2 = [t2] + targets[1:]
        assert diff_verse_targets("41004003", targets1, targets2) is None

    def test_non_equivalent_words_produce_diff(self, targets: list[Target]) -> None:
        """Replacing a word with a non-equivalent word produces a diff."""
        t1 = dataclasses.replace(targets[0], text="hello")
        t2 = dataclasses.replace(targets[0], text="world")
        targets1 = [t1] + targets[1:]
        targets2 = [t2] + targets[1:]
        record = diff_verse_targets("41004003", targets1, targets2)
        assert record is not None


# _bcvid_span doesn't reference instance state, so call it via the unbound method.
def _bcvid_span(bcvid: str) -> tuple[str, ...]:
    return DiffTargets84._bcvid_span(MagicMock(spec=DiffTargets84), bcvid)


class TestBcvidSpan:
    """Tests for DiffTargets84._bcvid_span."""

    def test_returns_three_tuple(self) -> None:
        """Result is always a 3-tuple."""
        result = _bcvid_span("41004003")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_middle_is_input(self) -> None:
        """The middle element always equals the input bcvid."""
        bcvid = "41004003"
        assert _bcvid_span(bcvid)[1] == bcvid

    def test_typical_verse(self) -> None:
        """Mid-chapter verse returns previous and next verse in same chapter."""
        assert _bcvid_span("41004003") == ("41004002", "41004003", "41004004")

    def test_previous_verse_decrements(self) -> None:
        """Previous verse number is one less than the input."""
        previous, _, _ = _bcvid_span("41004010")
        assert previous == "41004009"

    def test_next_verse_increments(self) -> None:
        """Next verse number is one more than the input."""
        _, _, next_ = _bcvid_span("41004010")
        assert next_ == "41004011"

    def test_book_chapter_prefix_preserved(self) -> None:
        """Book and chapter prefix is identical across all three elements."""
        result = _bcvid_span("40001015")
        assert all(v[:5] == "40001" for v in result)

    def test_verse_numbers_zero_padded(self) -> None:
        """Verse numbers are zero-padded to three digits."""
        previous, _, next_ = _bcvid_span("41004003")
        assert previous[-3:] == "002"
        assert next_[-3:] == "004"

    def test_verse_001_previous_is_000(self) -> None:
        """For verse 001, previous is verse 000 (no lower-bound guard)."""
        previous, _, _ = _bcvid_span("41004001")
        assert previous == "41004000"

    def test_all_elements_same_length(self) -> None:
        """All three bcvids have the same length as the input."""
        bcvid = "41004003"
        result = _bcvid_span(bcvid)
        assert all(len(v) == len(bcvid) for v in result)

    def test_different_book(self) -> None:
        """Works correctly for OT book numbers."""
        assert _bcvid_span("01001005") == ("01001004", "01001005", "01001006")


def _make_target(id: str, tokenstr: str) -> MagicMock:
    """Return a mock Target with id and tokenstr attributes."""
    t = MagicMock(spec=Target)
    t.id = id
    t.tokenstr = tokenstr
    return t


def _niv11map(instance: MagicMock, bcvid: str) -> dict[str, str]:
    """Call the real _niv11map implementation via the unbound method."""
    return DiffTargets84._niv11map(instance, bcvid)


def _rec11list(instance: MagicMock, alrec: MagicMock, niv11map: dict[str, str]) -> list[str]:
    """Call the real _rec11list implementation via the unbound method."""
    return DiffTargets84._rec11list(instance, alrec, niv11map)


def _make_dt84_mock(niv11bcvtargets: dict) -> MagicMock:
    """Return a minimal DiffTargets84 mock with niv11bcvtargets set and real _bcvid_span."""
    mock = MagicMock(spec=DiffTargets84)
    mock.niv11bcvtargets = niv11bcvtargets
    mock._bcvid_span = lambda bcvid: DiffTargets84._bcvid_span(mock, bcvid)
    return mock


class TestNiv11map:
    """Tests for DiffTargets84._niv11map."""

    def test_returns_dict(self) -> None:
        """_niv11map returns a dict."""
        mock = _make_dt84_mock({})
        result = _niv11map(mock, "41004003")
        assert isinstance(result, dict)

    def test_empty_when_no_targets(self) -> None:
        """Returns empty dict when niv11bcvtargets has no matching verse."""
        mock = _make_dt84_mock({})
        result = _niv11map(mock, "41004003")
        assert result == {}

    def test_includes_central_verse_targets(self) -> None:
        """Targets from the central verse are included."""
        t = _make_target("41004003001", "A")
        mock = _make_dt84_mock({"41004003": [t]})
        result = _niv11map(mock, "41004003")
        assert "41004003001" in result
        assert result["41004003001"] == "A"

    def test_includes_previous_verse_targets(self) -> None:
        """Targets from the previous verse (span[0]) are included."""
        t = _make_target("41004002001", "B")
        mock = _make_dt84_mock({"41004002": [t]})
        result = _niv11map(mock, "41004003")
        assert "41004002001" in result

    def test_includes_next_verse_targets(self) -> None:
        """Targets from the next verse (span[2]) are included."""
        t = _make_target("41004004001", "C")
        mock = _make_dt84_mock({"41004004": [t]})
        result = _niv11map(mock, "41004003")
        assert "41004004001" in result

    def test_all_three_verses_merged(self) -> None:
        """Targets from all three span verses appear in the result."""
        targets = {
            "41004002": [_make_target("41004002001", "prev")],
            "41004003": [_make_target("41004003001", "cur")],
            "41004004": [_make_target("41004004001", "next")],
        }
        mock = _make_dt84_mock(targets)
        result = _niv11map(mock, "41004003")
        assert set(result.keys()) == {"41004002001", "41004003001", "41004004001"}

    def test_maps_id_to_tokenstr(self) -> None:
        """Each key maps to the corresponding target's tokenstr."""
        t = _make_target("41004003001", "Behold")
        mock = _make_dt84_mock({"41004003": [t]})
        result = _niv11map(mock, "41004003")
        assert result["41004003001"] == "Behold"

    def test_multiple_tokens_per_verse(self) -> None:
        """Multiple tokens in a verse all appear in the result."""
        targets = [_make_target(f"4100400300{i}", f"word{i}") for i in range(1, 4)]
        mock = _make_dt84_mock({"41004003": targets})
        result = _niv11map(mock, "41004003")
        assert len(result) == 3


class TestRec11list:
    """Tests for DiffTargets84._rec11list."""

    def _mock_instance(self) -> MagicMock:
        mock = MagicMock(spec=DiffTargets84)
        mock.niv84_niv11_map = DiffTargets84.niv84_niv11_map
        return mock

    def _mock_alrec(self, selectors: list[str]) -> MagicMock:
        alrec = MagicMock()
        alrec.target_selectors = selectors
        return alrec

    def test_returns_list(self) -> None:
        """_rec11list returns a list."""
        mock = self._mock_instance()
        alrec = self._mock_alrec(["41004003001"])
        niv11map = {"41004003001": "A"}
        result = _rec11list(mock, alrec, niv11map)
        assert isinstance(result, list)

    def test_single_selector_direct_lookup(self) -> None:
        """A selector not in niv84_niv11_map is looked up directly in niv11map."""
        mock = self._mock_instance()
        alrec = self._mock_alrec(["41004003001"])
        niv11map = {"41004003001": "Behold"}
        result = _rec11list(mock, alrec, niv11map)
        assert result == ["Behold"]

    def test_multiple_selectors(self) -> None:
        """All selectors are resolved and returned in order."""
        mock = self._mock_instance()
        alrec = self._mock_alrec(["41004003001", "41004003002"])
        niv11map = {"41004003001": "A", "41004003002": "B"}
        result = _rec11list(mock, alrec, niv11map)
        assert result == ["A", "B"]

    def test_empty_selectors_returns_empty_list(self) -> None:
        """Empty target_selectors produces an empty list."""
        mock = self._mock_instance()
        alrec = self._mock_alrec([])
        result = _rec11list(mock, alrec, {})
        assert result == []

    def test_niv84_niv11_map_remaps_selector(self) -> None:
        """A selector present in niv84_niv11_map is remapped before niv11map lookup."""
        mock = self._mock_instance()
        # 41007021021 -> 41007022001 is in the class-level niv84_niv11_map
        alrec = self._mock_alrec(["41007021021"])
        niv11map = {"41007022001": "remapped_word"}
        result = _rec11list(mock, alrec, niv11map)
        assert result == ["remapped_word"]

    def test_missing_key_raises_keyerror(self) -> None:
        """KeyError is raised when a (possibly remapped) selector is absent from niv11map."""
        mock = self._mock_instance()
        alrec = self._mock_alrec(["41004003999"])
        with pytest.raises(KeyError):
            _rec11list(mock, alrec, {})

    def test_unmapped_selector_identity(self) -> None:
        """A selector not in niv84_niv11_map is used as-is (identity mapping)."""
        mock = self._mock_instance()
        sel = "41004003001"
        assert sel not in DiffTargets84.niv84_niv11_map
        alrec = self._mock_alrec([sel])
        niv11map = {sel: "direct"}
        result = _rec11list(mock, alrec, niv11map)
        assert result == ["direct"]
