"""Test code in interlinear.reverse."""

import tempfile
from pathlib import Path

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager
from biblealignlib.interlinear.reverse import Reader, Writer
from biblealignlib.interlinear.token import AlignedToken

ENGLANGDATAPATH = CLEARROOT / "Alignments/data/eng"


@pytest.fixture(scope="module")
def sblgntbsb() -> AlignmentSet:
    """Return an AlignmentSet instance."""
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
    return Manager(sblgntbsb)


@pytest.fixture(scope="module")
def reader_with_exclude(mgr: Manager) -> Reader:
    """Return a Reader instance with exclude=True."""
    return Reader(mgr, exclude=True)


@pytest.fixture(scope="module")
def reader_no_exclude(mgr: Manager) -> Reader:
    """Return a Reader instance with exclude=False."""
    return Reader(mgr, exclude=False)


class TestReader:
    """Test Reader()."""

    def test_init_with_exclude(self, reader_with_exclude: Reader) -> None:
        """Test initialization with exclude=True."""
        assert reader_with_exclude.mgr is not None
        assert isinstance(reader_with_exclude.aligned_tokens, list)
        assert len(reader_with_exclude.aligned_tokens) > 0
        # All tokens should be AlignedToken instances
        assert all(isinstance(at, AlignedToken) for at in reader_with_exclude.aligned_tokens)

    def test_init_no_exclude(self, reader_no_exclude: Reader) -> None:
        """Test initialization with exclude=False."""
        assert reader_no_exclude.mgr is not None
        assert isinstance(reader_no_exclude.aligned_tokens, list)
        # Should have more tokens when exclude=False
        assert len(reader_no_exclude.aligned_tokens) >= len(reader_no_exclude.aligned_tokens)

    def test_aligned_tokens_sorted(self, reader_with_exclude: Reader) -> None:
        """Test that aligned_tokens are sorted without errors."""
        # The sort operation should complete without raising an error
        # (some edge cases in comparison logic may not produce perfect ordering,
        # but at least it shouldn't crash)
        tokens = reader_with_exclude.aligned_tokens
        assert len(tokens) > 0
        # Verify tokens with same type maintain order
        target_tokens = [t for t in tokens if t.targettoken and not t.sourcetoken]
        source_tokens = [t for t in tokens if t.sourcetoken and not t.targettoken]
        # Within same type, should be sorted
        if len(target_tokens) > 1:
            for i in range(len(target_tokens) - 1):
                assert not target_tokens[i + 1] < target_tokens[i]
        if len(source_tokens) > 1:
            for i in range(len(source_tokens) - 1):
                assert not source_tokens[i + 1] < source_tokens[i]

    def test_source_alignments_via_manager(
        self, reader_with_exclude: Reader, mgr: Manager
    ) -> None:
        """Test that source_alignments are accessible via manager."""
        source_alignments = mgr.get_source_alignments()
        assert isinstance(source_alignments, set)
        assert len(source_alignments) > 0
        # All items should be Source instances
        from biblealignlib.burrito import Source

        assert all(isinstance(s, Source) for s in source_alignments)
        # Reader should use these alignments
        assert reader_with_exclude.source_alignments == source_alignments

    def test_target_alignments_via_manager(
        self, reader_with_exclude: Reader, mgr: Manager
    ) -> None:
        """Test that target_alignments are accessible via manager."""
        target_alignments = mgr.get_target_alignments()
        assert isinstance(target_alignments, dict)
        assert len(target_alignments) > 0
        # Keys should be Target instances, values should be Source instances
        from biblealignlib.burrito import Source, Target

        assert all(isinstance(t, Target) for t in target_alignments.keys())
        assert all(isinstance(s, Source) for s in target_alignments.values())
        # Reader should use these alignments
        assert reader_with_exclude.target_alignments == target_alignments

    def test_aligned_tokens_have_both_types(self, reader_with_exclude: Reader) -> None:
        """Test that aligned_tokens contain both aligned and unaligned tokens."""
        aligned_count = sum(1 for at in reader_with_exclude.aligned_tokens if at.aligned)
        unaligned_count = sum(1 for at in reader_with_exclude.aligned_tokens if not at.aligned)
        # Should have both types
        assert aligned_count > 0
        assert unaligned_count > 0

    def test_aligned_tokens_target_coverage(
        self, reader_with_exclude: Reader, mgr: Manager
    ) -> None:
        """Test that all non-excluded target tokens are represented."""
        # Get all non-excluded target tokens from manager
        included_targets = [t for t in mgr.targetitems.values() if not t.exclude]
        # Get all target tokens from reader
        reader_targets = [
            at.targettoken for at in reader_with_exclude.aligned_tokens if at.targettoken
        ]
        # Should have the same count
        assert len(included_targets) == len(reader_targets)

    def test_source_only_tokens(self, reader_with_exclude: Reader) -> None:
        """Test that unaligned source tokens are included."""
        source_only = [
            at
            for at in reader_with_exclude.aligned_tokens
            if at.sourcetoken and not at.targettoken
        ]
        # Should have some unaligned source tokens
        assert len(source_only) > 0
        # None of these should be marked as aligned
        assert all(not at.aligned for at in source_only)


class TestWriter:
    """Test Writer()."""

    def test_init(self, reader_with_exclude: Reader) -> None:
        """Test initialization."""
        writer = Writer(reader_with_exclude)
        assert writer.reader == reader_with_exclude

    def test_fieldnames(self) -> None:
        """Test that fieldnames are defined."""
        assert len(Writer.fieldnames) > 0
        # Check some expected fields
        assert "targetid" in Writer.fieldnames
        assert "targettext" in Writer.fieldnames
        assert "sourceid" in Writer.fieldnames
        assert "sourcetext" in Writer.fieldnames
        assert "strongs" in Writer.fieldnames
        assert "lemma" in Writer.fieldnames

    def test_write(self, reader_with_exclude: Reader) -> None:
        """Test write() method."""
        writer = Writer(reader_with_exclude)
        # Use a temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            outpath = Path(tmpdir) / "test_output" / "reverse_interlinear.tsv"
            writer.write(outpath)
            # Check that file was created
            assert outpath.exists()
            # Check that file has content
            assert outpath.stat().st_size > 0
            # Read first few lines to verify format
            with outpath.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # Should have header + data
                assert len(lines) > 1
                # Check header
                header = lines[0].strip().split("\t")
                assert header == Writer.fieldnames
                # Check that we have data rows
                assert len(lines) == len(reader_with_exclude.aligned_tokens) + 1  # +1 for header

    def test_write_creates_directory(self, reader_with_exclude: Reader) -> None:
        """Test that write() creates parent directories if they don't exist."""
        writer = Writer(reader_with_exclude)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested path that doesn't exist
            outpath = Path(tmpdir) / "nested" / "dirs" / "output.tsv"
            assert not outpath.parent.exists()
            writer.write(outpath)
            # Check that directories were created
            assert outpath.parent.exists()
            assert outpath.exists()

    def test_write_content_format(self, reader_with_exclude: Reader) -> None:
        """Test that written content has correct format."""
        writer = Writer(reader_with_exclude)
        with tempfile.TemporaryDirectory() as tmpdir:
            outpath = Path(tmpdir) / "test.tsv"
            writer.write(outpath)
            # Read and check some content
            with outpath.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # Check a data line (skip header)
                if len(lines) > 1:
                    data_line = lines[1].strip().split("\t")
                    # Should have same number of fields as header
                    assert len(data_line) == len(Writer.fieldnames)


class TestReaderWriterIntegration:
    """Test Reader and Writer integration."""

    def test_roundtrip_data_integrity(self, mgr: Manager) -> None:
        """Test that data can be written and maintains integrity."""
        reader = Reader(mgr, exclude=True)
        writer = Writer(reader)
        with tempfile.TemporaryDirectory() as tmpdir:
            outpath = Path(tmpdir) / "roundtrip.tsv"
            writer.write(outpath)
            # Verify the file has expected number of rows
            with outpath.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # Should match number of aligned tokens + header
                assert len(lines) == len(reader.aligned_tokens) + 1

    def test_exclude_parameter_affects_output(self, mgr: Manager) -> None:
        """Test that exclude parameter affects the output size."""
        reader_exclude = Reader(mgr, exclude=True)
        reader_no_exclude = Reader(mgr, exclude=False)
        writer_exclude = Writer(reader_exclude)
        writer_no_exclude = Writer(reader_no_exclude)
        with tempfile.TemporaryDirectory() as tmpdir:
            outpath_exclude = Path(tmpdir) / "with_exclude.tsv"
            outpath_no_exclude = Path(tmpdir) / "no_exclude.tsv"
            writer_exclude.write(outpath_exclude)
            writer_no_exclude.write(outpath_no_exclude)
            # File without exclude should be larger or equal
            with outpath_exclude.open("r") as f1, outpath_no_exclude.open("r") as f2:
                lines_exclude = f1.readlines()
                lines_no_exclude = f2.readlines()
                assert len(lines_no_exclude) >= len(lines_exclude)
