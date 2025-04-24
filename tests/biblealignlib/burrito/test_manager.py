"""Test manager.py and local imports."""

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, VerseData

# test published version
# ENGLANGDATAPATH = DATAPATH / "eng"
ENGLANGDATAPATH = CLEARROOT / "Alignments/data/eng"


@pytest.fixture(scope="module")
def sblgntbsb() -> AlignmentSet:
    """Return a AlignmentSet instance."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )


@pytest.fixture(scope="module")
def mgr(sblgntbsb: AlignmentSet) -> Manager:
    """Return a Manager instance."""
    mgr: Manager = Manager(sblgntbsb)
    return mgr


class TestManager:
    """Test manager.Manager()."""

    def test_init(self, mgr: Manager) -> None:
        """Test initialization."""
        assert mgr.alignmentset.sourceid == "SBLGNT"
        assert mgr.alignmentset.targetid == "BSB"
        assert mgr.sourceitems["41004003001"].lemma == "ἀκούω"
        assert mgr.targetitems["41004003002"].text == "Listen"

    def test_versedata(self, mgr: Manager) -> None:
        """Test VerseData."""
        vd44: VerseData = mgr["41004004"]
        assert vd44.alignments[0][0][0].lemma == "καί"
        assert vd44.targets_included[0].text == "And"
        assert vd44.get_texts(unique=True) == [
            "And",
            "as",
            "he",
            "was",
            "sowing",
            "some",
            "seed",
            "fell",
            "along",
            "the",
            "path",
            "and",
            "the.1",
            "birds",
            "came",
            "and.1",
            "devoured",
            "it",
        ]
        assert vd44.get_texts(typeattr="sources") == [
            "καὶ",
            "ἐγένετο",
            "ἐν",
            "τῷ",
            "σπείρειν",
            "ὃ",
            "μὲν",
            "ἔπεσεν",
            "παρὰ",
            "τὴν",
            "ὁδόν",
            "καὶ",
            "ἦλθεν",
            "τὰ",
            "πετεινὰ",
            "καὶ",
            "κατέφαγεν",
            "αὐτό",
        ]


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


# Should add tests for Reason/BadRecord
