# How to Load an Alignment Set

This guide shows how to configure an `AlignmentSet` and load it with a `Manager` for various source/target combinations.

## NT Greek → English (SBLGNT / BSB)

```python
from biblealignlib.burrito import AlignmentSet, Manager, CLEARROOT

alset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "Alignments/data/eng",
    alternateid="manual",
)
mgr = Manager(alset)
```

## OT Hebrew → English (WLCM / BSB)

```python
alset = AlignmentSet(
    sourceid="WLCM",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "Alignments/data/eng",
    alternateid="manual",
)
mgr = Manager(alset)
```

## Other Target Languages

Replace `targetlanguage` and `langdatapath` to point to any language-specific data directory:

```python
alset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="IRVHin",
    targetlanguage="hin",
    langdatapath=CLEARROOT / "alignments-hin/data",
    alternateid="manual",
)
mgr = Manager(alset)
```

## Verifying File Paths

Before loading, you can check that all expected files exist:

```python
alset.check_files()    # Raises FileNotFoundError if anything is missing
print(alset.sourcepath)
print(alset.targetpath)
print(alset.alignmentpath)
```

## Available Source IDs

```python
from biblealignlib import SourceidEnum

for src in SourceidEnum:
    print(src.value, "→", SourceidEnum.get_canon(src.value))
# SBLGNT → nt
# BGNT   → nt
# WLC    → ot
# WLCM   → ot
```

## Checking for Bad Records

`Manager` automatically detects and discards malformed alignment records. Check for any issues after loading:

```python
mgr = Manager(alset)
bad = mgr.alignmentsreader.badrecords
if bad:
    print(f"{len(bad)} bad records found:")
    for rec_id, reasons in list(bad.items())[:5]:
        print(f"  {rec_id}: {[r.reason.value for r in reasons]}")
```

See [Reference: BadRecord](../reference/burrito.md#badrecord) for the full list of error types.

## Loading Without Cleaning Bad Records

By default, bad records are removed. To keep them for inspection:

```python
mgr = Manager(alset, keepbadrecords=True)
```
