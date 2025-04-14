"""Determine what order to select chapters in, based on the vocabulary they add.

>>> from biblealignlib import CLEARROOT
>>> from biblealignlib.util import vocab
>>> mxm = vocab.LemmaSetMaximizer(CLEARROOT / "alignments-eng/data/")

"""

import copy
from pathlib import Path

# from typing import List, Tuple, Set

from ..burrito import SourceReader, groupby_bcid


class LemmaSetMaximizer:

    def __init__(self, sourcepath: Path):
        self.sourceitems: SourceReader = SourceReader(sourcepath)
        self.bcids: dict[str, list[str]] = groupby_bcid(self.sourceitems)
        self.doc_lemmas: dict[str, set[str]] = {
            bcid: set(self.sourceitems[bcvw].lemma for bcvw in self.bcids[bcid])
            for bcid in self.bcids
        }
        self.gcm = self.greedy_vocab_maximization(copy.copy(self.doc_lemmas))

    def greedy_vocab_maximization(self, doc_lemmas) -> list[tuple[str, set[str]]]:
        """
        Select chapters in order of how much new vocabulary they contribute,
        using a greedy algorithm.

        Args:
        chapters: List of chapter IDs, where each document is a set of lemmatized tokens.

        Returns:
        List of tuples (doc_index, new_vocab_count) in selection order.
        """
        remaining_docs = doc_lemmas
        selected_docs = []
        seen_vocab: set[str] = set()

        while remaining_docs:
            best_doc = None
            best_new_words = set()

            for bcid in remaining_docs:
                doc_vocab = self.doc_lemmas[bcid]
                new_words = doc_vocab - seen_vocab
                if len(new_words) > len(best_new_words):
                    best_doc = bcid
                    best_new_words = new_words

            if best_doc is None:  # No new vocab added; break early
                break

            seen_vocab.update(best_new_words)
            selected_docs.append((best_doc, best_new_words))
            # Remove the selected document from remaining_docs
            del remaining_docs[best_doc]

        return selected_docs

    def write_vocab(self, output_path: Path) -> None:
        """Write the vocabulary maximization results to a file."""
        book_ids = list(range(40, 67))
        book_chapters: dict[str, int] = {str(bid): 0 for bid in book_ids}
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("BCID\tBID\tchapters\tnew_vocab\t\n")
            for bcid, new_vocab in self.gcm:
                bid = bcid[:2]
                book_chapters[bid] += 1
                f.write(f"{bcid}\t{bid}\t{book_chapters[bid]}\t{len(new_vocab)}\n")
