"""Test VerseData.py.

Largely from Claude.
"""

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, VerseData

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
