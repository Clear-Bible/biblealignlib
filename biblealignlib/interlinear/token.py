"""Represent a token 'cell' for interlinears/reverse-interlinears."""

from dataclasses import dataclass, field
from typing import Optional

from ..burrito.source import Source
from ..burrito.target import Target


@dataclass
class AlignedToken:
    """An aligned set of source and target tokens.

    One or both
    """

    targettoken: Optional[Target] = None
    sourcetoken: Optional[Source] = None
    # if false, one or both tokens could be empty
    aligned: bool = False

    def __repr__(self) -> str:
        """Return a printed representation."""
        if self.targettoken:
            alignflag: str = ", aligned" if self.aligned else ""
            return f"<AlignedToken(targetid={self.targettoken.id}{alignflag})>"
        elif self.sourcetoken:
            return f"<AlignedToken(sourceid={self.sourcetoken.id})>"
        else:
            return "<AlignedToken(no token)>"

    # comparison methods for sorting
    # self+target, other+target: compare targets
    # self+target, other-target:
    #    self+source, other+source: compare sources
    #    self-source, other+source: compare self.target and other.source ids
    #    other-source: should not happen
    # self-target, other+target:
    #    self+source, other+source: compare sources
    #    self+source, other-source: compare self.source and other.target ids
    #    self-source: should not happen

    def __lt__(self: "AlignedToken", other: "AlignedToken") -> bool:
        if self.targettoken and other.targettoken:
            return self.targettoken < other.targettoken
        elif self.targettoken and not other.targettoken:
            if self.sourcetoken and other.sourcetoken:
                return self.sourcetoken < other.sourcetoken
            elif not self.sourcetoken and other.sourcetoken:
                # how to sort this?
                # lame hack: compare (incomparable) self.target and other.source
                return self.targettoken.id < other.sourcetoken.id
            elif not other.sourcetoken:
                raise ValueError("Cannot compare: other has neither target nor source.")
            else:
                raise ValueError("Cannot compare: unknown error.")
        elif not self.targettoken and other.targettoken:
            if self.sourcetoken and other.sourcetoken:
                return self.sourcetoken < other.sourcetoken
            elif self.sourcetoken and not other.sourcetoken:
                # how to sort this?
                # lame hack: compare (incomparable) target and source IDs
                return self.sourcetoken.id < other.targettoken.id
            elif not self.sourcetoken:
                raise ValueError("Cannot compare: self has neither target nor source.")
            else:
                raise ValueError("Cannot compare: unknown error.")

    def display(self) -> str:
        """Return a (target, source) string of the tokens IDs."""
        idstr = ""
        idstr += f" {self.targettoken.id}" if self.targettoken else f" {'-' * 11}"
        idstr += f" {self.sourcetoken.id}" if self.sourcetoken else f" {'-' * 11}"
        return idstr

    def ids(self) -> str:
        """Return a (source, target) string of the tokens IDs."""
        idstr = ""
        if self.sourcetoken:
            idstr = f"{self.sourcetoken.id}"
        else:
            idstr = "-" * 11
        if self.targettoken:
            idstr += f" {self.targettoken.id}"
        else:
            idstr += f" {'-' * 11}"
        return idstr

    def asdict(self) -> dict[str, str]:
        """Return a dictionary of the token details.

        Some attributes are renamed to keep them distinct.
        """
        atdict: dict[str, str] = {}
        if self.targettoken:
            atdict = self.targettoken.asdict()
            atdict["targetid"] = self.targettoken.id
            atdict["targettext"] = self.targettoken.text
            del atdict["id"], atdict["text"]
        if self.sourcetoken:
            atdict.update(self.sourcetoken.asdict())
            atdict["sourceid"] = self.sourcetoken.id
            atdict["sourcetext"] = self.sourcetoken.text
            del atdict["id"], atdict["text"]
        return atdict
