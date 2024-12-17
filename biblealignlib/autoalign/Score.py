"""Manage scores for alignment data."""

from dataclasses import dataclass, field
from typing import Optional

from biblealignlib.burrito import Source, Target, VerseData


def precision(true_positives: int, false_positives: int) -> float:
    denom = true_positives + false_positives
    return true_positives / denom if denom else 0


def recall(true_positives: int, false_negatives: int) -> float:
    denom = true_positives + false_negatives
    return true_positives / denom if denom else 0


def f1(recall: float, precision: float) -> float:
    denom = precision + recall
    return ((2 * precision * recall) / denom) if denom else 0


@dataclass
class _BaseScore:
    """Manage base scoring metrics."""

    identifier: str = ""
    true_positives: int = 0
    # true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    aer: float = 0.0

    def compute_metrics(self) -> None:
        """Compute various metrics."""
        self.precision = precision(self.true_positives, self.false_positives)
        self.aer = 1 - self.precision
        self.recall = recall(self.true_positives, self.false_negatives)
        self.f1 = f1(self.recall, self.precision)

    # should use summary_dict here
    def summary(self, width: int = 4, brief: bool = True) -> str:
        """Return summary metrics."""
        plabel = "P" if brief else "Precision"
        rlabel = "R" if brief else "Recall"
        return f"{self.identifier}: AER={self.aer:.{width}f}\t{plabel}={self.precision:.{width}f}\t{rlabel}={self.recall:.{width}f}\tF1={self.f1:.{width}f}"

    def summary_dict(self, width: int = 4) -> dict[str, str]:
        """Return a dict with summary scores."""
        return {
            "AER": f"{self.aer:.{width}f}",
            "F1": f"{self.f1:.{width}f}",
            "Precision": f"{self.precision:.{width}f}",
            "Recall": f"{self.recall:.{width}f}",
        }


    def __repr__(self) -> str:
        """Return a string representation of the Score."""
        return f"<{self.__class__.__name__}: {self.identifier}>"
    

@dataclass(repr=False)
class VerseScore(_BaseScore):
    """Manage scoring data for a verse."""

    # not really optional, but dataclass inheritance requires this
    reference: Optional[VerseData] = None
    hypothesis: Optional[VerseData] = None
    # computed
    n_sources: int = 0
    n_targets: int = 0
    referencepairs: list[tuple[Source, Target]] = field(init=False, default_factory=list)
    hypothesispairs: list[tuple[Source, Target]] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        """Compute values on initialization."""
        self.identifier = self.reference.bcvid
        self.n_sources = len(self.reference.sources)
        self.n_targets = len(self.reference.targets)
        # decompose into pairs of source and target indices
        self._get_pairs()
        # set operations on pairs: no partial credit
        self.true_positives = len(set(self.referencepairs) & set(self.hypothesispairs))
        self.false_positives = len(set(self.hypothesispairs) - set(self.referencepairs))
        self.false_negatives = len(set(self.referencepairs) - set(self.hypothesispairs))
        # sets values for P, R, F1, AER
        self.compute_metrics()

    def _get_pairs(self) -> None:
        """Populate reference/hypothesispairs."""
        # these are like pharaoh: tokens are repeated for multiple alignments
        self.referencepairs = self.reference.get_pairs()
        self.hypothesispairs = self.hypothesis.get_pairs()



@dataclass(repr=False)
class EssentialVerseScore(VerseScore):
    """Like VerseScore but only for essential alignments."""

    def _get_pairs(self) -> None:
        """Populate reference/hypothesispairs."""
        # these are like pharaoh: tokens are repeated for multiple alignments
        self.referencepairs = self.reference.get_pairs(essential=True)
        self.hypothesispairs = self.hypothesis.get_pairs(essential=True)


@dataclass(repr=False)
class GroupScore(_BaseScore):
    """Manage scoring data for a group of verses."""

    verse_scores: list[VerseScore] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Compute values on initialization."""
        assert self.identifier, "Must provide identifier"
        assert self.verse_scores, "Must provide verse_scores."

        self.true_positives: int = sum(v.true_positives for v in self.verse_scores)
        self.false_positives: int = sum(v.false_positives for v in self.verse_scores)
        self.false_negatives: int = sum(v.false_negatives for v in self.verse_scores)
        self.compute_metrics()
