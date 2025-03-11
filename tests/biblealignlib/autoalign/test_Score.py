"""Test score"""

import pytest

from biblealignlib.autoalign import Score
from biblealignlib.burrito import CLEARROOT, AlignmentSet, AlignmentsReader

# test internal version
ENGLANGDATAPATH = CLEARROOT / "alignments-eng/data"


@pytest.fixture
def sblgntbsb() -> AlignmentSet:
    """Return a AlignmentSet instance."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )


@pytest.fixture
def alreader(sblgntbsb: AlignmentSet) -> AlignmentsReader:
    """Return a AlignmentsReader instance."""
    return AlignmentsReader(sblgntbsb)


class TestMetrics:

    def test_precision(self) -> None:
        assert Score.precision(80, 20) == 0.8
        assert Score.precision(0, 0) == 0.0

    def test_recall(self) -> None:
        assert Score.recall(80, 20) == 0.8
        assert Score.recall(0, 0) == 0.0

    def test_f1(self) -> None:
        assert round(Score.f1(0.8, 0.9), 2) == 0.85
        assert Score.f1(0, 0) == 0.0

    # def test_mcc(self) -> None:
    #     assert round(Score.mcc(80, 20, 40, 0), 2) == 0.73
    #     # denom = (80 + 20) * (80 + 40) * (0 + 20) * (0 + 40)
    #     assert Score.mcc(0, 0) == 0.0


class Test_BaseScore:

    def test_init(self) -> None:
        """Test initialization."""
        bs = Score._BaseScore(true_positives=80, false_positives=20, false_negatives=40)
        bs.compute_metrics()
        assert bs.precision == 0.8
        assert round(bs.recall, 2) == 0.67
        assert round(bs.f1, 2) == 0.73
        assert round(bs.aer, 2) == 0.2
        # assert round(bs.mcc, 2) == 0.47


# class TestVerseScore:

#     def test_init(self) -> None:
#         """Test initialization."""
#         versescore = Score.VerseScore(truth, hypothesis)
