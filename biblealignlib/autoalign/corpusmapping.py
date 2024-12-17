"""Manages corpus data for auto alignment."""

from dataclasses import dataclass, field

from biblealignlib.burrito import (
    BaseToken,
    Source,
    Target,
)


@dataclass
class CorpusMapping:
    """Map corpus instances to pharaoh-data for a single verse correspondence.

    bcv is based on source versification: targets with different
    versifications should be mapped to comparable source verses in the
    TSV.

    Example: Target:01031005007 corresponds to Source:01032001

    """

    # BCV-format verse reference
    bcv: str
    # Source instances and their pharaoh indices
    source_pairs: list[tuple[Source, int]] = field(default_factory=list)
    # Target instances and their pharaoh indices
    target_pairs: list[tuple[Target, int]] = field(default_factory=list)
    _typeattrs: tuple = ("sources", "targets")
    # these values computed in post_init
    # dict: index -> Token
    sourceindexmap: dict[int, BaseToken] = field(default_factory=dict)
    targetindexmap: dict[int, BaseToken] = field(default_factory=dict)
    # dict: Token -> index
    sourcetokenmap: dict[BaseToken, int] = field(default_factory=dict)
    targettokenmap: dict[BaseToken, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Compute values after initialization."""
        self.sourceindexmap = {index: item for item, index in self.source_pairs}
        self.targetindexmap = {index: item for item, index in self.target_pairs}
        self.sourcetokenmap = dict(self.source_pairs)
        self.targettokenmap = dict(self.target_pairs)

    def __repr__(self) -> str:
        """Return a string representation of the CorpusMapping."""
        return f"<CorpusMapping: {self.bcv}>"

    def tokenids(self, typeattr: str) -> list[str]:
        """Return the list of corpus token ids for typeattr."""
        assert typeattr in self._typeattrs, f"typeattr should be one of {self._typeattrs}"
        pairs = self.source_pairs if typeattr == "sources" else self.target_pairs
        return [corpus.id for corpus, _ in pairs]

    def indices(self, typeattr: str) -> list[str]:
        """Return the list of pharaoah indices for typeattr."""
        assert typeattr in self._typeattrs, f"typeattr should be one of {self._typeattrs}"
        pairs = self.source_pairs if typeattr == "sources" else self.target_pairs
        return [index for _, index in pairs]

    def tokentexts(self, typeattr: str) -> list[str]:
        """Return the list of corpus token texts for typeattr."""
        assert typeattr in self._typeattrs, f"typeattr should be one of {self._typeattrs}"
        pairs = self.source_pairs if typeattr == "sources" else self.target_pairs
        return [corpus.text for corpus, _ in pairs]

    def display(self, typeattr: str) -> None:
        """Print out the id and text pairs for debugging."""
        assert typeattr in self._typeattrs, f"typeattr should be one of {self._typeattrs}"
        pairs = self.source_pairs if typeattr == "sources" else self.target_pairs
        for token, index in pairs:
            print(f"{index}: {token.id}, {token.text}")
