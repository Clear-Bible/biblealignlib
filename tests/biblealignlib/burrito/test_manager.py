"""Test manager.py and local imports."""

import pytest

from biblealignlib.burrito import CLEARROOT, AlignmentSet, Manager, VerseData, Source, Target

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
            # minor difference in word order here 2025-12-16: did the text change?!?
            "came",
            "the.1",
            "birds",
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

    def test_get_source_alignments(self, mgr: Manager) -> None:
        """Test get_source_alignments() returns set of aligned sources."""
        source_alignments = mgr.get_source_alignments()
        # Should be a set
        assert isinstance(source_alignments, set)
        # Should contain Source instances
        from biblealignlib.burrito import Source

        assert all(isinstance(s, Source) for s in source_alignments)
        # Should have aligned sources
        assert len(source_alignments) > 0
        # Check that we have sources from multiple verses
        bcvs = {s.bcv for s in source_alignments}
        assert len(bcvs) > 1

        # check the actual SBLGNT-BSB alignments for MAT 1:1!8
        assert mgr.sourceitems["40001001008"] in source_alignments  # Ἐν
        assert mgr.sourceitems["40001002003"] not in source_alignments  # τὸν

    # don't need to test for uniqueness separately since set guarantees that
    # don't need to test that alignments are a subset: logic guarantees that

    def test_get_target_alignments(self, mgr: Manager) -> None:
        """Test get_target_alignments() returns dict mapping targets to list of sources."""
        target_alignments = mgr.get_target_alignments()
        # Should be a dict
        assert isinstance(target_alignments, dict)
        # Should have entries
        assert len(target_alignments) > 0

        assert all(isinstance(t, Target) for t in target_alignments.keys())
        assert all(isinstance(sources, list) for sources in target_alignments.values())
        assert all(
            isinstance(s, Source)
            for sourcelists in target_alignments.values()
            for sources in sourcelists
            for s in sources
        )
        # Check that aligned targets from verse data appear in the mapping
        vd = mgr["41004003"]
        if vd.alignments:
            # Get first alignment
            sources, targets = vd.alignments[0]
            if sources and targets:
                # Targets should be in the mapping
                assert targets[0] in target_alignments
                # The mapped sources should be a list
                mapped_sources = target_alignments[targets[0]]
                assert isinstance(mapped_sources, list)
                assert len(mapped_sources) > 0
                assert all(
                    isinstance(s, Source) for sourcelists in mapped_sources for s in sourcelists
                )

    def test_unaligned_sourcebcv(self, mgr: Manager) -> None:
        """Test unaligned_sourcebcv property."""
        # dependent on current alignment data: but this verse doesn't
        # occur in BSB so can't be aligned
        unaligned = mgr.unaligned_sourcebcv()
        assert "45016" in unaligned
        assert "45016024" in unaligned["45016"]

    def test_get_source_targets(self, mgr: Manager) -> None:
        """Test get_source_targets."""
        akouete = mgr.sourceitems["41004003001"]
        targetids = [trg.id for trg in mgr.get_source_targets(akouete)]
        assert ["41004003002"] == targetids
        sower = mgr.sourceitems["41004003006"]
        targetids = [trg.id for trg in mgr.get_source_targets(sower)]
        assert ["41004003008", "41004003009", "41004003010", "41004003011"] == targetids

    def test_get_source_targets_returns_target_instances(self, mgr: Manager) -> None:
        """Test get_source_targets() returns Target instances."""
        akouete = mgr.sourceitems["41004003001"]
        targets = mgr.get_source_targets(akouete)
        assert all(isinstance(t, Target) for t in targets)

    def test_get_source_targets_unaligned_source(self, mgr: Manager, capsys) -> None:
        """Test get_source_targets() returns [] with warning for an unaligned source."""
        # Find a source token from a verse that has no alignment records
        unaligned_bcvs = mgr.unaligned_sourcebcv()
        assert unaligned_bcvs, "Expected at least one unaligned source BCV for this dataset"
        # Pick the first BCV and its first source token
        first_chap = next(iter(unaligned_bcvs))
        first_bcv = unaligned_bcvs[first_chap][0]
        source_tokens = mgr.bcv["sources"].get(first_bcv)
        assert source_tokens, f"No source tokens found for {first_bcv}"
        result = mgr.get_source_targets(source_tokens[0])
        captured = capsys.readouterr()
        assert result == []
        assert "Warning" in captured.out

    def test_token_alignments_source_lemma(self, mgr: Manager) -> None:
        """Test token_alignments() finds records by source lemma."""
        records = mgr.token_alignments("ἀκούω", role="source", tokenattr="lemma")
        assert isinstance(records, list)
        assert len(records) > 0
        # Every returned record must contain a source token with that lemma
        for rec in records:
            source_tokens = [mgr.sourceitems[sel] for sel in rec.source_selectors]
            assert any(tok.lemma == "ἀκούω" for tok in source_tokens)

    def test_token_alignments_target_text(self, mgr: Manager) -> None:
        """Test token_alignments() finds records by target text."""
        records = mgr.token_alignments("Listen", role="target", tokenattr="text")
        assert isinstance(records, list)
        assert len(records) > 0
        for rec in records:
            target_tokens = [mgr.targetitems[sel] for sel in rec.target_selectors]
            assert any(tok.text == "Listen" for tok in target_tokens)

    def test_token_alignments_no_match(self, mgr: Manager) -> None:
        """Test token_alignments() returns empty list for a term that doesn't exist."""
        records = mgr.token_alignments("XXXXNOTAWORD", role="source", tokenattr="text")
        assert records == []

    def test_display_record(self, mgr: Manager) -> None:
        """Test display_record() returns a non-empty string."""
        # Use first alignment record available
        first_records = mgr.alignmentsreader.alignmentgroup.records
        assert first_records
        result = mgr.display_record(first_records[0])
        assert isinstance(result, str)
        assert "Sources" in result
        assert "Targets" in result

    # dropped some other superfluous tests


# Should add tests for Reason/BadRecord
