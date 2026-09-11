"""Test AlignmentsReader."""

import pytest

from biblealignlib.burrito import (
    CLEARROOT,
    AlignmentSet,
    AlignmentsReader,
    AlignmentRecord,
    unwrap_group,
)

# test internal version
ENGLANGDATAPATH = CLEARROOT / "alignments-eng/data"


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
def alreader(sblgntbsb: AlignmentSet) -> AlignmentsReader:
    """Return a AlignmentsReader instance."""
    return AlignmentsReader(sblgntbsb)


class TestUnwrapGroup:
    """Test unwrap_group()."""

    def test_enveloped(self) -> None:
        """Test that a 0.4 file's group is read from inside "groups"."""
        data = {"format": "alignment", "version": "0.4", "groups": [{"type": "translation"}]}
        assert unwrap_group(data) == {"type": "translation"}

    def test_bare_group(self) -> None:
        """Test that a bare group is still read.

        Version 0.3 allowed a group-less top level, and published data
        is still written that way.
        """
        data = {"type": "translation", "records": []}
        assert unwrap_group(data) == data

    def test_multiple_groups_raises(self) -> None:
        """Test that several groups cannot be read as a single alignment set."""
        data = {"format": "alignment", "version": "0.4", "groups": [{}, {}]}
        with pytest.raises(ValueError):
            unwrap_group(data)


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
