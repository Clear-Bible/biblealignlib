"""Utilities used for burrito data.


>>> from biblealignlib.burrito import util

# group target tokens by verse
>>> from biblealignlib import CLEARROOT
>>> tr = target.TargetReader(CLEARROOT / "alignments-eng/data/targets/BSB/nt_BSB.tsv")
>>> vd = util.groupby_bcv(tr.values())
# tokens for MRK 4:3
>>> vd["41004003"]
[<Target: 41004003001>, <Target: 41004003002>, <Target: 41004003003>, <Target: 41004003004>, ...]

"""

from itertools import groupby
from typing import Any, Callable
import warnings

from .BaseToken import BaseToken


# this is general so belongs in Clearlib: cleanup needed
def groupby_key(
    # maybe really Iterable?
    items: list[Any],
    key: Callable = lambda x: x,
) -> dict[str, list[Any]]:
    """Group a list of items into a dict by their key values.

    key function should return a string for each item. This is
    intended to be easily repurposed for other items and keys.
    """
    return {k: list(g) for k, g in groupby(sorted(items, key=key), key)}


def groupby_bcv(values: list[Any], bcvfn: Callable = BaseToken.to_bcv) -> dict[str, list[Any]]:
    """Group a list of tokens into a dict by their BCV values."""
    return {k: list(g) for k, g in groupby(values, bcvfn)}


def token_groupby_bc(items: list[str | BaseToken]) -> dict[str, list[Any]]:
    """Group a list of tokens into a dict by their BC (book+chapter) values."""

    def _to_bc(token: BaseToken) -> str:
        if isinstance(token, BaseToken):
            return token.id[:5]
        elif isinstance(token, str):
            return token[:5]
        else:
            raise ValueError(f"Invalid type for {token}")

    return groupby_key(items, key=_to_bc)


def groupby_bcid(values: list[str]) -> dict[str, list[Any]]:
    """Group a list of token ids into a dict by their BC (book+chapter) values."""

    def _to_bc(tokenid: str) -> str:
        return tokenid[:5]

    return {k: list(g) for k, g in groupby(values, _to_bc)}


def filter_by_bcv(
    items: list[Any],
    startbcv: str,
    endbcv: str,
    key: Callable = lambda x: x,
) -> list[Any]:
    """Return a subset of items matching start/endbcv.

    key is the function to apply to elements of items to get a bcv
    string to compare. This assumes the items are in canonical order.
    """
    partial: list[Any] = []
    collecting: bool = False
    for item in items:
        itembcv = key(item)
        if itembcv == startbcv:
            collecting = True
        if collecting:
            partial.append(item)
        if itembcv == endbcv:
            collecting = False
            break
    if not partial:
        raise ValueError(f"No records: didn't find startbcv {startbcv}")
    if collecting:
        lastbcv = key(list(items)[-1])
        if endbcv != lastbcv:
            warnings.warn(f"Did not stop collecting: check endbcv {endbcv}")
    return partial
