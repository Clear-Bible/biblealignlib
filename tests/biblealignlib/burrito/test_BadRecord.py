"""Test BadRecord detection and handling."""

import pytest

from biblealignlib.burrito import (
    Source,
    Target,
    SourceReader,
    TargetReader,
    Document,
    Metadata,
    AlignmentReference,
    AlignmentRecord,
    TranslationType,
)
from biblealignlib.burrito.alignments import bad_reason
from biblealignlib.burrito.BadRecord import BadRecord, Reason


@pytest.fixture(scope="module")
def sample_sources() -> SourceReader:
    """Return a minimal SourceReader for testing."""
    from collections import UserDict

    class MockSourceReader(UserDict):
        """Mock SourceReader for testing."""

        def __init__(self):
            super().__init__()
            self.data = {
                "40001001001": Source(
                    id="40001001001",
                    text="Βίβλος",
                    strong="G0976",
                    gloss="Book",
                    lemma="βίβλος",
                    pos="noun",
                ),
                "40001001002": Source(
                    id="40001001002",
                    text="γενέσεως",
                    strong="G1078",
                    gloss="genealogy",
                    lemma="γένεσις",
                    pos="noun",
                ),
            }

    return MockSourceReader()


@pytest.fixture(scope="module")
def sample_targets() -> TargetReader:
    """Return a minimal TargetReader for testing."""
    from collections import UserDict

    class MockTargetReader(UserDict):
        """Mock TargetReader for testing."""

        def __init__(self):
            super().__init__()
            self.data = {
                "40001001001": Target(id="40001001001", text="book", exclude=False),
                "40001001002": Target(id="40001001002", text="of", exclude=False),
                "40001001003": Target(id="40001001003", text="the", exclude=True),  # excluded
                "40001001004": Target(id="40001001004", text="genealogy", exclude=False),
            }

    return MockTargetReader()


def create_test_record(
    rec_id: str, source_sels: list[str], target_sels: list[str]
) -> AlignmentRecord:
    """Helper function to create test AlignmentRecords."""
    meta = Metadata(id=rec_id, origin="test", status="created")
    source_doc = Document(docid="SBLGNT", scheme="BCVWP")
    target_doc = Document(docid="BSB", scheme="BCVW")

    source_ref = AlignmentReference(document=source_doc, selectors=source_sels)
    target_ref = AlignmentReference(document=target_doc, selectors=target_sels)

    return AlignmentRecord(
        meta=meta, references={"source": source_ref, "target": target_ref}, type=TranslationType()
    )


class TestBadRecords:
    """Test BadRecord detection and handling."""

    def test_nosource(self, sample_sources: SourceReader, sample_targets: TargetReader) -> None:
        """Test detection of records with no source selectors."""
        rec = create_test_record("test.001", [], ["40001001001"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert isinstance(bad, BadRecord)
        assert bad.reason == Reason.NOSOURCE
        assert bad.identifier == "test.001"
        assert "NOSOURCE" in bad.display

    def test_emptysource(self, sample_sources: SourceReader, sample_targets: TargetReader) -> None:
        """Test detection of records with empty string in source selectors."""
        rec = create_test_record("test.002", ["40001001001", ""], ["40001001001"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert bad.reason == Reason.EMPTYSOURCE
        assert bad.identifier == "test.002"
        assert "EMPTYSOURCE" in bad.display

    def test_notarget(self, sample_sources: SourceReader, sample_targets: TargetReader) -> None:
        """Test detection of records with no target selectors."""
        rec = create_test_record("test.003", ["40001001001"], [])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert bad.reason == Reason.NOTARGET
        assert bad.identifier == "test.003"
        assert "NOTARGET" in bad.display

    def test_emptytarget(self, sample_sources: SourceReader, sample_targets: TargetReader) -> None:
        """Test detection of records with empty string in target selectors."""
        rec = create_test_record("test.004", ["40001001001"], ["40001001001", ""])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert bad.reason == Reason.EMPTYTARGET
        assert bad.identifier == "test.004"
        assert "EMPTYTARGET" in bad.display

    def test_missingsource(
        self, sample_sources: SourceReader, sample_targets: TargetReader
    ) -> None:
        """Test detection of records with missing source token IDs."""
        rec = create_test_record("test.005", ["40001001999"], ["40001001001"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert bad.reason == Reason.MISSINGSOURCE
        assert bad.identifier == "test.005"
        assert bad.data == ("40001001999",)
        assert "MISSINGSOURCE" in bad.display
        assert "40001001999" in bad.display

    def test_missingtargetall(
        self, sample_sources: SourceReader, sample_targets: TargetReader
    ) -> None:
        """Test detection of records where all target token IDs are missing."""
        rec = create_test_record("test.006", ["40001001001"], ["40001001999", "40001001998"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert bad.reason == Reason.MISSINGTARGETALL
        assert bad.identifier == "test.006"
        assert set(bad.data) == {"40001001999", "40001001998"}
        assert "MISSINGTARGETALL" in bad.display

    def test_missingtargetsome(
        self, sample_sources: SourceReader, sample_targets: TargetReader
    ) -> None:
        """Test detection of records where some target token IDs are missing."""
        rec = create_test_record("test.007", ["40001001001"], ["40001001001", "40001001999"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert bad.reason == Reason.MISSINGTARGETSOME
        assert bad.identifier == "test.007"
        assert bad.data == ("40001001999",)
        assert "MISSINGTARGETSOME" in bad.display

    def test_alignedexclude(
        self, sample_sources: SourceReader, sample_targets: TargetReader
    ) -> None:
        """Test detection of records with excluded tokens aligned."""
        # 40001001003 is marked as exclude=True in sample_targets
        rec = create_test_record("test.008", ["40001001001"], ["40001001003"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        assert bad.reason == Reason.ALIGNEDEXCLUDE
        assert bad.identifier == "test.008"
        assert bad.data == ("40001001003",)
        assert "ALIGNEDEXCLUDE" in bad.display

    def test_good_record(self, sample_sources: SourceReader, sample_targets: TargetReader) -> None:
        """Test that valid records return None (no error)."""
        rec = create_test_record("test.009", ["40001001001"], ["40001001001"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is None

    def test_multiple_sources_and_targets(
        self, sample_sources: SourceReader, sample_targets: TargetReader
    ) -> None:
        """Test valid record with multiple sources and targets."""
        rec = create_test_record(
            "test.010", ["40001001001", "40001001002"], ["40001001001", "40001001002"]
        )
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is None

    def test_badrecord_repr(
        self, sample_sources: SourceReader, sample_targets: TargetReader
    ) -> None:
        """Test BadRecord __repr__ method."""
        rec = create_test_record("test.011", ["40001001999"], ["40001001001"])
        bad = bad_reason(rec, sample_sources, sample_targets)

        assert bad is not None
        repr_str = repr(bad)
        assert "BadRecord" in repr_str
        assert "test.011" in repr_str
        assert "Token reference is missing" in repr_str
        assert "40001001999" in repr_str

    def test_badrecord_display_formats(
        self, sample_sources: SourceReader, sample_targets: TargetReader
    ) -> None:
        """Test that BadRecord.display formats correctly for different reasons."""
        # Test ALIGNEDEXCLUDE format
        rec1 = create_test_record("test.012", ["40001001001"], ["40001001003"])
        bad1 = bad_reason(rec1, sample_sources, sample_targets)
        if bad1:
            assert "Targets:" in bad1.display

        # Test MISSINGSOURCE format
        rec2 = create_test_record("test.013", ["40001001999"], ["40001001001"])
        bad2 = bad_reason(rec2, sample_sources, sample_targets)
        if bad2:
            assert "Missing sources:" in bad2.display
            assert "targets:" in bad2.display

        # Test MISSINGTARGETSOME format
        rec3 = create_test_record("test.014", ["40001001001"], ["40001001001", "40001001999"])
        bad3 = bad_reason(rec3, sample_sources, sample_targets)
        if bad3:
            assert "Sources:" in bad3.display
            assert "Missing targets:" in bad3.display
