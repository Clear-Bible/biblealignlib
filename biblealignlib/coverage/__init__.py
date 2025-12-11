"""Coverage analysis package for biblealignlib.

Provides tools for assessing alignment coverage at token, verse, and book levels.
"""

from biblealignlib import CLEARROOT

from .analyzer import CoverageAnalyzer
from .Coverage import BookCoverage, GroupCoverage, TokenCoverage, VerseCoverage
from .exporter import CoverageExporter
from .filters import CoverageFilter

__all__ = [
    "CLEARROOT",
    # Coverage dataclasses
    "TokenCoverage",
    "VerseCoverage",
    "BookCoverage",
    "GroupCoverage",
    # analyzer
    "CoverageAnalyzer",
    # exporter
    "CoverageExporter",
    # filters
    "CoverageFilter",
]
