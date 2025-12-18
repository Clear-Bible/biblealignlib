"""Code for working with alignment data in Scripture Burrito format."""

# where Clear-Bible repos are rooted
from biblealignlib import CLEARROOT, SOURCES

from .reverse import Reader, Writer

__all__ = [
    "CLEARROOT",
    "SOURCES",
    "Reader",
    "Writer",
]
