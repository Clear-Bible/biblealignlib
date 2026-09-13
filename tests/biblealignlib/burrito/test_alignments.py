"""Test AlignmentsReader."""

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, AlignmentsReader, AlignmentRecord
from biblealignlib.burrito.alignments import declared_schemes

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


class TestDeclaredSchemes:
    """Test declared_schemes()."""

    def test_documents_are_read(self) -> None:
        """Test that the scheme each document declares is returned."""
        agroupdict = {
            "documents": [
                {"docid": "SBLGNT", "scheme": "BCVWP"},
                {"docid": "BSB", "scheme": "BCVW"},
            ]
        }
        assert declared_schemes(agroupdict) == {"SBLGNT": "BCVWP", "BSB": "BCVW"}

    def test_no_documents_declares_nothing(self) -> None:
        """Test that a file with no documents array declares no schemes.

        Nothing is invented to fill the gap: an absent declaration is
        reported as absent.
        """
        assert declared_schemes({"records": []}) == {}

    def test_a_document_without_a_scheme_is_omitted(self) -> None:
        """Test that a document declaring no scheme contributes none."""
        agroupdict = {"documents": [{"docid": "SBLGNT"}, {"docid": "BSB", "scheme": "BCVW"}]}
        assert declared_schemes(agroupdict) == {"BSB": "BCVW"}


class TestAlignmentsReader:
    """Test AlignmentsReader()."""

    def test_init(self, alreader: AlignmentsReader) -> None:
        """Test initialization."""
        assert alreader.sourcedoc.docid == "SBLGNT"
        assert alreader.targetdoc.docid == "BSB"

    def test_schemes_come_from_the_file(self, alreader: AlignmentsReader) -> None:
        """Test that each document's scheme is the one the file declares.

        The reader used to assert BCVWP for both documents and then
        rewrite the target's, discarding whatever the file said.
        """
        assert alreader.sourcedoc.scheme == "BCVWP"
        assert alreader.targetdoc.scheme == "BCVW"
        assert not alreader.rejected
        algroup = alreader.alignmentgroup
        alrec: dict[str, AlignmentRecord] = {arec.meta.id: arec for arec in algroup.records}
        assert alrec["41004003.001"].asdict()["source"] == ["41004003001", "41004003002"]
        assert alrec["41004003.001"].meta.id == "41004003.001"
        assert alrec["41004003.001"].identifier == "41004003.001"
