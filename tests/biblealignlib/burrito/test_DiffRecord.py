"""Test DiffReason and DiffRecord."""

import pytest

from biblealignlib.burrito.DiffRecord import DiffReason, DiffRecord
from biblealignlib.burrito.source import Source
from biblealignlib.burrito.target import Target


class TestDiffReason:
    """Test DiffReason enum."""

    def test_values(self) -> None:
        """Test all enum values are present and correct."""
        assert DiffReason.DIFFLEN.value == "Different number of alignments"
        assert DiffReason.DIFFSOURCES.value == "Source selectors differ"
        assert DiffReason.DIFFTARGETS.value == "Target selectors differ"
        assert DiffReason.DIFFNOTES.value == "Different notes"
        assert DiffReason.DIFFSTATUS.value == "Different status"

    def test_members(self) -> None:
        """Test all expected members exist."""
        members = {r.name for r in DiffReason}
        assert members == {"DIFFLEN", "DIFFSOURCES", "DIFFTARGETS", "DIFFNOTES", "DIFFSTATUS"}


class TestDiffRecord:
    """Test DiffRecord dataclass."""

    def test_init_minimal(self) -> None:
        """Test initialization with only required field."""
        rec = DiffRecord(bcvid="41004003")
        assert rec.bcvid == "41004003"
        assert rec.sources1 == ()
        assert rec.targets1 == ()
        assert rec.sources2 == ()
        assert rec.targets2 == ()
        assert rec.diffreason is None
        assert rec.data == ()

    def test_init_with_reason(self) -> None:
        """Test initialization with a DiffReason."""
        rec = DiffRecord(bcvid="41004003", diffreason=DiffReason.DIFFLEN)
        assert rec.diffreason == DiffReason.DIFFLEN

    def test_init_with_all_fields(self) -> None:
        """Test initialization with all fields populated."""
        src1 = Source(id="41004003001", text="ἐξῆλθεν", strong="G1831", gloss="went out", lemma="ἐξέρχομαι", pos="verb")
        src2 = Source(id="41004003002", text="σπεῖραι", strong="G4687", gloss="to sow", lemma="σπείρω", pos="verb")
        tgt1 = Target(id="41004003001", text="went out")
        tgt2 = Target(id="41004003002", text="to sow")

        rec = DiffRecord(
            bcvid="41004003",
            sources1=(src1,),
            targets1=(tgt1,),
            sources2=(src2,),
            targets2=(tgt2,),
            diffreason=DiffReason.DIFFSOURCES,
            data=("extra",),
        )
        assert rec.bcvid == "41004003"
        assert rec.sources1 == (src1,)
        assert rec.targets1 == (tgt1,)
        assert rec.sources2 == (src2,)
        assert rec.targets2 == (tgt2,)
        assert rec.diffreason == DiffReason.DIFFSOURCES
        assert rec.data == ("extra",)

    def test_repr_with_reason(self) -> None:
        """Test __repr__ includes bcvid and reason value."""
        rec = DiffRecord(bcvid="41004003", diffreason=DiffReason.DIFFTARGETS)
        r = repr(rec)
        assert "41004003" in r
        assert DiffReason.DIFFTARGETS.value in r
        assert r.startswith("<DiffRecord")

    def test_repr_without_reason(self) -> None:
        """Test __repr__ when diffreason is None."""
        rec = DiffRecord(bcvid="41004003")
        r = repr(rec)
        assert "41004003" in r
        assert "None" in r
        assert r.startswith("<DiffRecord")

    def test_repr_with_data(self) -> None:
        """Test __repr__ includes data when present."""
        rec = DiffRecord(bcvid="41004003", diffreason=DiffReason.DIFFSTATUS, data=("old", "new"))
        r = repr(rec)
        assert "old" in r
        assert "new" in r

    def test_repr_without_data(self) -> None:
        """Test __repr__ omits data section when data is empty."""
        rec = DiffRecord(bcvid="41004003", diffreason=DiffReason.DIFFNOTES)
        r = repr(rec)
        # data tuple is empty, so repr should not append it
        assert r.endswith(">")
        # closing bracket comes right after the reason, not after data
        assert "(), " not in r

    def test_repr_all_reasons(self) -> None:
        """Test __repr__ works for every DiffReason."""
        for reason in DiffReason:
            rec = DiffRecord(bcvid="41004003", diffreason=reason)
            r = repr(rec)
            assert reason.value in r
