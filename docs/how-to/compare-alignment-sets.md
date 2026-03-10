# How to Compare Two Alignment Sets

## Diff a Single Verse

`VerseData.diff()` returns a list of `DiffRecord` instances describing differences between two verses:

```python
vd1 = mgr1["41004003"]
vd2 = mgr2["41004003"]

diffs = vd1.diff(vd2)
if diffs:
    for d in diffs:
        print(repr(d))   # <DiffRecord(41004003, DIFFPAIRS)>
else:
    print("Identical")
```

`DiffReason` values: `DIFFLEN` (different number of alignment groups), `DIFFPAIRS` (same length but different token sets).

## Merge Two Sets of Alignments with Merger

`Merger` compares two `Manager` instances for the same source, language, and target, combining their data:

```python
from biblealignlib.util.merger import Merger

# Both managers must share sourceid, targetid, and targetlanguage
merger = Merger(mgr1, mgr2)

# Summary of how many verses fall into each pairing category
print(merger.pairingcounts)
# Counter({'neither': 6191, 'mgr1': 1272, 'both': 475, 'mgr2': 1})

# Verses present in both sets but with different alignments
print(f"Differing overlaps: {len(merger.diffpairs)}")
merger.show_diffs()
```

## Perform a Safe Merge

`safe_merge()` combines records where there is no conflict:

- Verses in only `mgr1` → taken from `mgr1`
- Verses in only `mgr2` → taken from `mgr2`
- Verses in both with **no diffs** → taken from `mgr1` (they're identical)
- Verses in both **with diffs** → skipped (manual resolution required)

```python
merged_group = merger.safe_merge(verbose=True)
# mgr1 records: 1272
# after mgr2 records: 1273
# after both records: 1726

from biblealignlib.burrito import write_alignment_group
with open("merged.json", "w") as f:
    write_alignment_group(merged_group, f)
```

## Write the Merged Result

`Merger.write_merge()` writes the safe-merged group using a combined name:

```python
# Output file: {sourceid}-{targetid}-{alternateid1}{alternateid2}.json
merger.write_merge()
```

## BCVPair

Each verse comparison is stored as a `BCVPair`:

```python
from biblealignlib.util import BCVPair

pair = merger.bcv_pairs["41004003"]
print(pair.pairing)   # "both", "mgr1", "mgr2", or "neither"
print(pair.diffs)     # list of DiffRecord (empty if identical)
```

You can construct a `BCVPair` directly to compare two `VerseData` instances:

```python
pair = BCVPair(bcv="41004003", mgr1_data=vd1, mgr2_data=vd2)
print(pair.pairing)
print(pair.diffs)
```
