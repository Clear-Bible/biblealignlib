"""Utilities for working with Strong's numbers.

Obligatory disclaimer: Strong's numbers are a mess, and we shouldn't
rely on them. Nevertheless, some data comes with them, so we should
maintain them, and (when forced) use them.

"""

import re
import warnings

_STRONGSRE: re.Pattern = re.compile(r"[AGH]?\d{1,4}[a-d]?")
# any other alpha suffix is eliminated
_BADSUFFIXRE: re.Pattern = re.compile(r"[e-z]$")
SPECIALS: dict[str, str] = {
    "1537+4053": "G4053b",
    "5228+1537+4053": "G4053c",
    "1417+3461": "G3461b",
}


def normalize_strongs(strongs: str | int, prefix: str = "", strict: bool = False) -> str:
    """Return a normalized Strongs id.

    Args:
        strongs: Strong's number as string or int
        prefix: Optional prefix letter (A, G, H). If strongs is int,
            this must be specified.
        strict: If True, raise an error for empty Strong's codes with prefix='H'. Default is False.
    Returns:
        Normalized Strong's code as string.
    """
    # first handle any integer cases
    if isinstance(strongs, int):
        if prefix:
            return f"{prefix}{strongs:0>4}"
        else:
            raise ValueError("If strongs is int, prefix must be specified")
    # WLCM.tsv has some empty values: allow these if not strict
    if not strongs:
        if prefix == "H" and not strict:
            # no info, so nothing else we can return
            return ""
        else:
            raise ValueError("Strong's code must not be empty")
    # some special cases for SBLGNT data
    if strongs in SPECIALS:
        return SPECIALS[strongs]
    # some weird cases from WLCM with vertical bars, like
    # "1886j|2050b". Use the number after the bar, though that
    # sometimes seems wrong.
    if "|" in strongs:
        strongs = strongs.split("|")[-1]
    # special case for uW KeyTerms data: some like G29620. It appears
    # the last digit is always zero. This assumes there's always an initial prefix
    if strongs.startswith("G") and len(strongs) == 6 and strongs.endswith("0"):
        strongs = strongs[:-1]
    # some Macula Hebrew has trailing j, z
    if _BADSUFFIXRE.search(strongs):
        strongs = strongs[:-1]
    if _STRONGSRE.fullmatch(strongs):
        # check for initial prefix: save if available
        if re.match(r"[AGH]", strongs):
            firstchar = strongs[0]
            if prefix:
                if firstchar != prefix:
                    warnings.warn(f"Overwriting prefix parameter {prefix} for {strongs}")
            else:
                prefix = firstchar
        base = re.sub(r"\D", "", strongs)
        # final letter
        if re.search("[a-d]$", strongs):
            suffix = strongs[-1]
        else:
            suffix = ""
        # might need other tests here
        # this drops any suffix
        if not prefix:
            raise ValueError(f"prefix must be specified: {strongs}")
        return f"{prefix}{base:0>4}{suffix}"
    else:
        raise ValueError(f"Invalid Strong's code: {strongs}")
