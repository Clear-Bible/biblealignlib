"""Test code in biblealignlib/util/vocab.py."""

import pytest
from pathlib import Path

from biblealignlib.burrito import CLEARROOT
from biblealignlib.util.vocab import LemmaSetMaximizer

SBLGNT_TSV = CLEARROOT / "Alignments/data/sources/SBLGNT.tsv"


@pytest.fixture(scope="module")
def lsm() -> LemmaSetMaximizer:
    """Return a LemmaSetMaximizer for the SBLGNT source."""
    return LemmaSetMaximizer(SBLGNT_TSV)


class TestLemmaSetMaximizer:
    """Test LemmaSetMaximizer class."""

    def test_init(self, lsm: LemmaSetMaximizer) -> None:
        """Test initialization populates expected attributes."""
        assert lsm.sourceitems is not None
        assert isinstance(lsm.bcids, dict)
        assert len(lsm.bcids) > 0
        assert isinstance(lsm.doc_lemmas, dict)
        assert isinstance(lsm.gcm, list)

    def test_doc_lemmas_are_sets(self, lsm: LemmaSetMaximizer) -> None:
        """Each entry in doc_lemmas is a set of strings."""
        for bcid, lemmas in lsm.doc_lemmas.items():
            assert isinstance(lemmas, set)
            assert all(isinstance(l, str) for l in lemmas)

    def test_gcm_length(self, lsm: LemmaSetMaximizer) -> None:
        """GCM result has at most as many entries as there are chapter IDs."""
        assert len(lsm.gcm) <= len(lsm.bcids)

    def test_gcm_entries_are_tuples(self, lsm: LemmaSetMaximizer) -> None:
        """Each GCM entry is a (bcid, set) tuple."""
        for entry in lsm.gcm:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            bcid, new_vocab = entry
            assert isinstance(bcid, str)
            assert isinstance(new_vocab, set)

    def test_gcm_new_vocab_nonempty(self, lsm: LemmaSetMaximizer) -> None:
        """Each GCM entry contributes at least one new lemma."""
        for _, new_vocab in lsm.gcm:
            assert len(new_vocab) > 0

    def test_gcm_no_duplicate_bcids(self, lsm: LemmaSetMaximizer) -> None:
        """No chapter appears twice in GCM output."""
        bcids = [bcid for bcid, _ in lsm.gcm]
        assert len(bcids) == len(set(bcids))

    def test_gcm_vocab_disjoint(self, lsm: LemmaSetMaximizer) -> None:
        """New-vocab sets across GCM entries are pairwise disjoint."""
        seen: set[str] = set()
        for _, new_vocab in lsm.gcm:
            assert new_vocab.isdisjoint(seen), "Duplicate lemmas found across GCM entries"
            seen.update(new_vocab)

    def test_write_vocab(self, lsm: LemmaSetMaximizer, tmp_path: Path) -> None:
        """write_vocab() creates a file with a header and data rows."""
        output = tmp_path / "vocab.tsv"
        lsm.write_vocab(output)
        assert output.exists()
        lines = output.read_text(encoding="utf-8").splitlines()
        assert lines[0].startswith("BCID\tBID\tchapters\tnew_vocab")
        assert len(lines) > 1
