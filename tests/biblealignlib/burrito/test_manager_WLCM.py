"""Pull out this test that takes longer."""

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager

# test published version
# ENGLANGDATAPATH = DATAPATH / "eng"
ENGLANGDATAPATH = CLEARROOT / "Alignments/data/eng"


class TestWLCMManager:
    alset = AlignmentSet(
        sourceid="WLCM", targetid="BSB", targetlanguage="eng", langdatapath=ENGLANGDATAPATH
    )
    manager = Manager(alset)

    def test_init(self) -> None:
        """Test reading WLCM."""
        # target scheme should be downgraded
        # refactored
        # assert self.manager.targetdoc.scheme == "BCVW"
        assert self.alset.sourceid == "WLCM"
        assert self.alset.targetid == "BSB"
