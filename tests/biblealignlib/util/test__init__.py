"""Test code in biblealignlib/util/__init__.py."""

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, VerseData
from biblealignlib.util import BCVPair

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


class TestBCVPair:
    """Test BCVPair dataclass."""

    def test_both(self, mgr: Manager) -> None:
        """BCVPair with data from both managers has pairing='both'."""
        vd: VerseData = mgr["41004003"]
        pair = BCVPair(bcv="41004003", mgr1_data=vd, mgr2_data=vd)
        assert pair.pairing == "both"

    def test_both_identical_no_diffs(self, mgr: Manager) -> None:
        """BCVPair comparing a VerseData with itself has no diffs."""
        vd: VerseData = mgr["41004003"]
        pair = BCVPair(bcv="41004003", mgr1_data=vd, mgr2_data=vd)
        assert pair.diffs == []

    def test_mgr1_only(self, mgr: Manager) -> None:
        """BCVPair with only mgr1_data has pairing='mgr1'."""
        vd: VerseData = mgr["41004003"]
        pair = BCVPair(bcv="41004003", mgr1_data=vd)
        assert pair.pairing == "mgr1"
        assert pair.mgr2_data is None

    def test_mgr2_only(self, mgr: Manager) -> None:
        """BCVPair with only mgr2_data has pairing='mgr2'."""
        vd: VerseData = mgr["41004003"]
        pair = BCVPair(bcv="41004003", mgr2_data=vd)
        assert pair.pairing == "mgr2"
        assert pair.mgr1_data is None

    def test_neither(self) -> None:
        """BCVPair with no data has pairing='neither'."""
        pair = BCVPair(bcv="41004003")
        assert pair.pairing == "neither"
        assert pair.mgr1_data is None
        assert pair.mgr2_data is None

    def test_repr(self) -> None:
        """Test __repr__ includes bcv."""
        pair = BCVPair(bcv="41004003")
        assert repr(pair) == "<BCVPair(41004003)>"
