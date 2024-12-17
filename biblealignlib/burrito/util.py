"""Utilities used for burrito data.


>>> from biblealignlib.burrito import util

# group target tokens by verse
>>> from biblealignlib import ROOT
>>> tr = target.TargetReader(ROOT.parent.parent / "alignments-eng/data/targets/BSB/nt_BSB.tsv")
>>> vd = util.groupby_bcv(tr.values())
"""

from itertools import groupby
from typing import Any, Callable

from .BaseToken import BaseToken


def groupby_bcv(values: list[Any], bcvfn: Callable = BaseToken.to_bcv) -> dict[str, list[Any]]:
    """Group a list of tokens into a dict by their BCV values."""
    return {k: list(g) for k, g in groupby(values, bcvfn)}
