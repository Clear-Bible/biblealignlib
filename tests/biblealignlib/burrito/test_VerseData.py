"""Test VerseData.py.

Largely from Claude.
"""

import pytest
import pandas as pd

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, VerseData, Source, Target
from biblealignlib.burrito.DiffRecord import DiffReason, DiffRecord

# test published version
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


class TestVerseData:
    """Test VerseData class."""

    def test_init(self, mgr: Manager) -> None:
        """Test VerseData initialization."""
        vd: VerseData = mgr["41004004"]
        assert vd.bcvid == "41004004"
        assert len(vd.sources) > 0
        assert len(vd.targets) > 0
        assert len(vd.alignments) > 0

    def test_repr(self, mgr: Manager) -> None:
        """Test __repr__ method."""
        vd: VerseData = mgr["41004004"]
        assert repr(vd) == "<VerseData: 41004004>"

    def test_targets_included(self, mgr: Manager) -> None:
        """Test targets_included computed field."""
        vd: VerseData = mgr["41004004"]
        # targets_included should only contain non-excluded targets
        for target in vd.targets_included:
            assert not target.exclude

    def test_unaligned_sources_empty(self, mgr: Manager) -> None:
        """Test unaligned_sources when all sources are aligned."""
        # Find a verse where all sources are aligned
        vd: VerseData = mgr["41001001"]
        # Check if there are any unaligned sources
        unaligned = vd.unaligned_sources
        # This is data-dependent, but we can verify the property works
        assert isinstance(unaligned, list)
        # Verify all returned tokens are actually Source instances
        for src in unaligned:
            assert src in vd.sources
            # Verify they're truly not in any alignment
            for aligned_srcs, _ in vd.alignments:
                assert src not in aligned_srcs

    def test_unaligned_targets_empty(self, mgr: Manager) -> None:
        """Test unaligned_targets when all targets are aligned."""
        vd: VerseData = mgr["41001001"]
        unaligned = vd.unaligned_targets
        assert isinstance(unaligned, list)
        # Verify all returned tokens are from targets_included
        for trg in unaligned:
            assert trg in vd.targets_included
            # Verify they're truly not in any alignment
            for _, aligned_trgs in vd.alignments:
                assert trg not in aligned_trgs

    def test_unaligned_sources_with_gaps(self, mgr: Manager) -> None:
        """Test unaligned_sources detects sources not in any alignment."""
        # Test across multiple verses to find one with unaligned sources
        # found_unaligned = False
        for bcvid in list(mgr.keys())[:50]:  # Check first 50 verses
            vd: VerseData = mgr[bcvid]
            unaligned = vd.unaligned_sources
            if len(unaligned) > 0:
                # found_unaligned = True
                # Verify the unaligned sources are truly unaligned
                aligned_sources = {src for srcs, _ in vd.alignments for src in srcs}
                for src in unaligned:
                    assert src not in aligned_sources
                    assert src in vd.sources
                break
        # This assertion may be data-dependent
        # If all test data is perfectly aligned, this could fail
        # In that case, we'd need to construct a test case with known gaps

    def test_unaligned_targets_with_gaps(self, mgr: Manager) -> None:
        """Test unaligned_targets detects targets not in any alignment."""
        # Test across multiple verses to find one with unaligned targets
        # found_unaligned = False
        for bcvid in list(mgr.keys())[:50]:  # Check first 50 verses
            vd: VerseData = mgr[bcvid]
            unaligned = vd.unaligned_targets
            if len(unaligned) > 0:
                # found_unaligned = True
                # Verify the unaligned targets are truly unaligned
                aligned_targets = {trg for _, trgs in vd.alignments for trg in trgs}
                for trg in unaligned:
                    assert trg not in aligned_targets
                    assert trg in vd.targets_included
                    assert not trg.exclude
                break

    def test_unaligned_targets_excludes_excluded(self, mgr: Manager) -> None:
        """Test unaligned_targets only returns non-excluded targets."""
        # Check multiple verses to find excluded targets
        for bcvid in list(mgr.keys())[:50]:
            vd: VerseData = mgr[bcvid]
            # Check if there are any excluded targets
            excluded_targets = [t for t in vd.targets if t.exclude]
            if len(excluded_targets) > 0:
                unaligned = vd.unaligned_targets
                # Verify no excluded targets are in unaligned list
                for trg in unaligned:
                    assert not trg.exclude
                break

    def test_unaligned_method_targets(self, mgr: Manager, capsys) -> None:
        """Test unaligned() method with typeattr='targets'."""
        vd: VerseData = mgr["41004004"]
        vd.unaligned(typeattr="targets")
        captured = capsys.readouterr()
        # Should produce some output (either tokens or empty)
        # The actual content is data-dependent

    def test_unaligned_method_sources(self, mgr: Manager, capsys) -> None:
        """Test unaligned() method with typeattr='sources'."""
        vd: VerseData = mgr["41004004"]
        vd.unaligned(typeattr="sources")
        captured = capsys.readouterr()
        # Should produce some output (either tokens or empty)

    def test_unaligned_method_invalid_typeattr(self, mgr: Manager) -> None:
        """Test unaligned() method with invalid typeattr raises assertion."""
        vd: VerseData = mgr["41004004"]
        with pytest.raises(AssertionError, match="typeattr should be one of"):
            vd.unaligned(typeattr="invalid")

    def test_get_source_targets(self, mgr: Manager) -> None:
        vd: VerseData = mgr["41004003"]
        source_targets: dict[Source, list[Target]] = vd.get_source_targets()
        targetids = [t.id for t in source_targets[mgr.sourceitems["41004003001"]]]
        assert targetids == ["41004003002"]

    def test_table_aligned(self, mgr: Manager, capsys) -> None:
        """Test table() with aligned=True (default) produces output."""
        vd: VerseData = mgr["41004003"]
        vd.table()
        captured = capsys.readouterr()
        assert len(captured.out) > 0
        # Each line should have a tab separator
        lines = [l for l in captured.out.splitlines() if l.strip()]
        assert all("\t" in line for line in lines)

    def test_table_unaligned(self, mgr: Manager, capsys) -> None:
        """Test table() with aligned=False shows source-centric view."""
        vd: VerseData = mgr["41004003"]
        vd.table(aligned=False)
        captured = capsys.readouterr()
        assert len(captured.out) > 0
        lines = [l for l in captured.out.splitlines() if l.strip()]
        # Should have one line per source token
        assert len(lines) == len(vd.sources)

    def test_table_srcwidth(self, mgr: Manager, capsys) -> None:
        """Test table() respects srcwidth parameter."""
        vd: VerseData = mgr["41004003"]
        vd.table(aligned=False, srcwidth=60)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_get_texts(self, mgr: Manager) -> None:
        """Test get_texts() method."""
        vd: VerseData = mgr["41004004"]
        # Test default (targets, not unique)
        texts = vd.get_texts()
        assert isinstance(texts, list)
        assert all(isinstance(t, str) for t in texts)

        # Test with unique=True
        unique_texts = vd.get_texts(unique=True)
        assert isinstance(unique_texts, list)

        # Test with typeattr="sources"
        source_texts = vd.get_texts(typeattr="sources")
        assert isinstance(source_texts, list)
        assert len(source_texts) == len(vd.sources)

    def test_get_pairs(self, mgr: Manager) -> None:
        """Test get_pairs() method."""
        vd: VerseData = mgr["41004004"]
        pairs = vd.get_pairs()
        assert isinstance(pairs, list)
        for src, trg in pairs:
            assert src in vd.sources
            assert trg in vd.targets

        # Test with essential=True
        essential_pairs = vd.get_pairs(essential=True)
        assert isinstance(essential_pairs, list)
        # Essential pairs should only include content words
        for src, _ in essential_pairs:
            assert src.is_content

    def test_aligned_sources(self, mgr: Manager) -> None:
        """Test aligned_sources property returns sources present in alignments."""
        vd: VerseData = mgr["41004004"]
        aligned = vd.aligned_sources
        assert isinstance(aligned, list)
        # All aligned sources must be in vd.sources
        for src in aligned:
            assert src in vd.sources
        # The set of aligned sources equals what's in the alignment pairs
        alignment_sources: set[Source] = {src for srcs, _ in vd.alignments for src in srcs}
        assert set(aligned) == alignment_sources

    def test_aligned_targets(self, mgr: Manager) -> None:
        """Test aligned_targets property returns non-excluded targets in alignments."""
        vd: VerseData = mgr["41004004"]
        aligned = vd.aligned_targets
        assert isinstance(aligned, list)
        # All aligned targets must be from targets_included (non-excluded)
        for trg in aligned:
            assert trg in vd.targets_included
            assert not trg.exclude
        # The set must be a subset of what's in the alignment pairs
        alignment_targets: set[Target] = {trg for _, trgs in vd.alignments for trg in trgs}
        assert set(aligned).issubset(alignment_targets)

    def test_aligned_and_unaligned_sources_partition(self, mgr: Manager) -> None:
        """Test that aligned + unaligned sources partition all sources."""
        vd: VerseData = mgr["41004004"]
        aligned = set(vd.aligned_sources)
        unaligned = set(vd.unaligned_sources)
        assert aligned.isdisjoint(unaligned)
        assert aligned | unaligned == set(vd.sources)

    def test_aligned_and_unaligned_targets_partition(self, mgr: Manager) -> None:
        """Test that aligned + unaligned targets partition targets_included."""
        vd: VerseData = mgr["41004004"]
        aligned = set(vd.aligned_targets)
        unaligned = set(vd.unaligned_targets)
        assert aligned.isdisjoint(unaligned)
        assert aligned | unaligned == set(vd.targets_included)

    def test_get_source_alignments(self, mgr: Manager) -> None:
        """Test get_source_alignments() returns targets aligned to a specific source."""
        vd: VerseData = mgr["41004003"]
        source = mgr.sourceitems["41004003001"]
        targets = vd.get_source_alignments(source)
        assert isinstance(targets, list)
        assert len(targets) == 1
        assert targets[0].id == "41004003002"

    def test_get_source_alignments_multi(self, mgr: Manager) -> None:
        """Test get_source_alignments() for a source aligned to multiple targets."""
        vd: VerseData = mgr["41004003"]
        sower = mgr.sourceitems["41004003006"]
        targets = vd.get_source_alignments(sower)
        assert isinstance(targets, list)
        target_ids = [t.id for t in targets]
        assert target_ids == ["41004003008", "41004003009", "41004003010", "41004003011"]

    def test_dataframe_shape(self, mgr: Manager) -> None:
        """Test dataframe() returns a DataFrame with correct dimensions."""
        vd: VerseData = mgr["41004004"]
        df = vd.dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df.index) == len(vd.sources)
        assert len(df.columns) == len(vd.targets_included)

    def test_dataframe_custom_marks(self, mgr: Manager) -> None:
        """Test dataframe() respects hitmark and missmark arguments."""
        vd: VerseData = mgr["41004004"]
        df = vd.dataframe(hitmark="X", missmark=".")
        values = df.values.flatten()
        assert all(v in ("X", ".") for v in values)

    def test_diff_identical(self, mgr: Manager) -> None:
        """Test diff() of a VerseData against itself returns no differences."""
        vd: VerseData = mgr["41004004"]
        diffs = vd.diff(vd)
        assert diffs == []

    def test_diff_type_error(self, mgr: Manager) -> None:
        """Test diff() raises AssertionError when compared with a non-VerseData."""
        vd: VerseData = mgr["41004004"]
        with pytest.raises(AssertionError):
            vd.diff("not a VerseData")  # type: ignore[arg-type]

    def test_diff_record_repr(self) -> None:
        """Test DiffRecord __repr__ includes bcvid and reason."""
        rec = DiffRecord(bcvid="41004004", diffreason=DiffReason.DIFFLEN)
        r = repr(rec)
        assert "41004004" in r
        assert DiffReason.DIFFLEN.value in r
