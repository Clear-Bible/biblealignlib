"""Code for working with alignment data in Scripture Burrito format."""

# where Clear-Bible repos are rooted
from biblealignlib import CLEARROOT, SOURCES

from .AlignmentGroup import (
    Document,
    Metadata,
    AlignmentReference,
    AlignmentRecord,
    AlignmentGroup,
    TopLevelGroups,
)

from .AlignmentSet import AlignmentSet

# probably don't need the other types
from .AlignmentType import TranslationType
from .alignments import AlignmentsReader, write_alignment_group
from .manager import Manager, VerseData
from .BaseToken import BaseToken, asbool, bare_id
from .source import macula_prefixer, macula_unprefixer, Source, SourceReader
from .target import Target, TargetReader


__all__ = [
    "CLEARROOT",
    "SOURCES",
    # AlignmentGroup
    "Document",
    "Metadata",
    "AlignmentReference",
    "AlignmentRecord",
    "AlignmentGroup",
    "TopLevelGroups",
    # AlignmentSet
    "AlignmentSet",
    # AlignmentType
    "TranslationType",
    # BaseToken
    "BaseToken",
    "asbool",
    "bare_id",
    # alignments
    "AlignmentsReader",
    "write_alignment_group",
    # manager
    "Manager",
    "VerseData",
    # source
    "macula_prefixer",
    "macula_unprefixer",
    "Source",
    "SourceReader",
    # target
    "Target",
    "TargetReader",
    "TargetWriter",
    # util
    "groupby_bcv",
]
