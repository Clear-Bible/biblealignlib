"""Test code in biblealignlib/util/merger.py."""

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, AlignmentGroup, Manager
from biblealignlib.util.merger import Merger

ENGLANGDATAPATH = CLEARROOT / "Alignments/data/eng"


@pytest.fixture(scope="module")
def mgr() -> Manager:
    """Return a Manager instance for SBLGNT-BSB (manual)."""
    alset = AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )
    return Manager(alset)


@pytest.fixture(scope="module")
def merger(mgr: Manager) -> Merger:
    """Return a Merger of a manager with itself."""
    return Merger(mgr, mgr)


class TestMerger:
    """Test Merger class."""

    def test_init(self, merger: Merger) -> None:
        """Test basic Merger initialization."""
        assert merger.mgr1 is merger.mgr2
        assert isinstance(merger.bcv_pairs, dict)
        assert len(merger.bcv_pairs) > 0

    def test_pairingcounts_keys(self, merger: Merger) -> None:
        """Pairing counts contain expected keys."""
        keys = set(merger.pairingcounts.keys())
        # When merging a manager with itself, all verses with data are 'both',
        # verses with no data are 'neither'
        assert keys <= {"both", "neither", "mgr1", "mgr2"}

    def test_pairingcounts_sum(self, merger: Merger) -> None:
        """Sum of pairing counts equals total number of BCV pairs."""
        total = sum(merger.pairingcounts.values())
        assert total == len(merger.bcv_pairs)

    def test_overlaps(self, merger: Merger) -> None:
        """Overlaps list contains only 'both' pairings."""
        for bcvpair in merger.overlaps:
            assert bcvpair.pairing == "both"

    def test_diffpairs_subset_of_overlaps(self, merger: Merger) -> None:
        """diffpairs is a subset of overlaps."""
        overlap_bcvs = {b.bcv for b in merger.overlaps}
        for bcvpair in merger.diffpairs:
            assert bcvpair.bcv in overlap_bcvs

    def test_self_merge_no_diffs(self, merger: Merger) -> None:
        """Merging a manager with itself produces no diffpairs."""
        assert merger.diffpairs == []

    def test_get_bcv_pairs_coverage(self, merger: Merger, mgr: Manager) -> None:
        """get_bcv_pairs covers all source BCV ids."""
        assert set(merger.bcv_pairs.keys()) == set(mgr.bcv["sources"])

    def test_safe_merge_returns_alignment_group(self, merger: Merger) -> None:
        """safe_merge() returns an AlignmentGroup."""
        result = merger.safe_merge(verbose=False)
        assert isinstance(result, AlignmentGroup)

    def test_safe_merge_record_count(self, merger: Merger, mgr: Manager) -> None:
        """safe_merge() of identical managers returns same record count."""
        result = merger.safe_merge(verbose=False)
        original = mgr.alignmentsreader.alignmentgroup
        assert len(result.records) == len(original.records)

    def test_add_records_no_duplication(self, merger: Merger) -> None:
        """add_records() raises AssertionError on duplicate source selectors."""
        algroup = merger.mgr1.alignmentsreader.alignmentgroup
        if algroup.records:
            duplicate = algroup.records[0]
            with pytest.raises(AssertionError):
                merger.add_records(algroup, (duplicate,))

    def test_show_diffs_runs(self, merger: Merger, capsys) -> None:
        """show_diffs() runs without error."""
        merger.show_diffs()
        # No diffs when merging with itself, so output may be minimal
        capsys.readouterr()
