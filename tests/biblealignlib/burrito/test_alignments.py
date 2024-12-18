"""Test AlignmentsReader."""

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, AlignmentsReader, AlignmentRecord

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


class TestAlignmentsReader:
    """Test AlignmentsReader()."""

    def test_init(self, alreader: AlignmentsReader) -> None:
        """Test initialization."""
        assert alreader.scheme == "BCVWP"
        assert alreader.sourcedoc.docid == "SBLGNT"
        assert alreader.targetdoc.docid == "BSB"
        assert not alreader.rejected
        algroup = alreader.alignmentgroup
        alrec: dict[str, AlignmentRecord] = {arec.meta.id: arec for arec in algroup.records}
        assert alrec["41004003.001"].asdict()["source"] == ["41004003001", "41004003002"]
        assert alrec["41004003.001"].meta.id == "41004003.001"
        assert alrec["41004003.001"].identifier == "41004003.001"
