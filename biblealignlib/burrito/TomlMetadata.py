"""Read the TOML sidecar that accompanies an alignment file.

Each published alignment has a TOML file beside it recording who holds
rights over the texts, over their tokenizations, and over the alignment
itself, along with licences and source URLs. A Scripture Burrito requires
that information, and the TOML is the only place it exists, so it has to
be read when converting an alignment to burrito form.

The sections are kept distinct rather than merged. A source text, the
tokenization of that text, and the alignment built from it may each be
held by a different party, and the licences involved require attribution
to the right one.

>>> meta = TomlMetadata.from_path(alignmentset.tomlpath)
>>> meta.alignment.team
'Biblica'
>>> meta.source.metadata.tokenization
''
"""

from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import Any


@dataclass
class Provenance:
    """Rights over the tokenization or annotation of a text.

    Distinct from rights over the text itself: a text may be published by
    one party and tokenized by another.
    """

    copyright: str = ""
    license: str = ""
    # the tokenizer that produced the identifiers, where one is named
    tokenization: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Provenance":
        """Return an instance for a [source.metadata] or [target.metadata] table."""
        return cls(
            copyright=data.get("copyright", ""),
            license=data.get("license", ""),
            tokenization=data.get("tokenization", ""),
        )


@dataclass
class TextInfo:
    """A source or target text, and the rights over it."""

    identifier: str = ""
    copyright: str = ""
    license: str = ""
    # free prose qualifying the licence, where the publisher supplies it
    licensenotes: str = ""
    url: str = ""
    # localized names keyed by language code, from 'name.eng = "..."'
    name: dict[str, str] = field(default_factory=dict)
    # rights over this text's tokenization, not over the text
    metadata: Provenance = field(default_factory=Provenance)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextInfo":
        """Return an instance for a [source] or [target] table."""
        return cls(
            identifier=data.get("identifier", ""),
            copyright=data.get("copyright", ""),
            license=data.get("license", ""),
            licensenotes=data.get("licensenotes", ""),
            url=data.get("url", ""),
            name=dict(data.get("name", {})),
            metadata=Provenance.from_dict(data.get("metadata", {})),
        )


@dataclass
class AlignmentInfo:
    """The alignment itself, and the rights over it."""

    identifier: str = ""
    copyright: str = ""
    license: str = ""
    # the format the sidecar claims the alignment conforms to
    format: str = ""
    origin: str = ""
    process: str = ""
    # "NT", "OT", or a USFM book abbreviation
    scope: str = ""
    team: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlignmentInfo":
        """Return an instance for an [alignment] table."""
        return cls(
            identifier=data.get("identifier", ""),
            copyright=data.get("copyright", ""),
            license=data.get("license", ""),
            format=data.get("format", ""),
            origin=data.get("origin", ""),
            process=data.get("process", ""),
            scope=data.get("scope", ""),
            team=data.get("team", ""),
        )


@dataclass
class TomlMetadata:
    """The contents of an alignment's TOML sidecar."""

    source: TextInfo = field(default_factory=TextInfo)
    target: TextInfo = field(default_factory=TextInfo)
    alignment: AlignmentInfo = field(default_factory=AlignmentInfo)

    @classmethod
    def from_path(cls, path: Path) -> "TomlMetadata":
        """Return an instance read from the TOML file at path.

        Raises ValueError naming the path if the file cannot be parsed.
        """
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as err:
            raise ValueError(f"Could not parse {path}: {err}") from err
        return cls(
            source=TextInfo.from_dict(data.get("source", {})),
            target=TextInfo.from_dict(data.get("target", {})),
            alignment=AlignmentInfo.from_dict(data.get("alignment", {})),
        )
