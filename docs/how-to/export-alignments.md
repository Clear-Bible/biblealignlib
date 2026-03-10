# How to Export Alignment Data

## Write an Alignment Group to JSON

```python
from biblealignlib.burrito import write_alignment_group

group = mgr.alignmentsreader.alignmentgroup

with open("output.json", "w") as f:
    write_alignment_group(group, f)
```

The output follows the Scripture Burrito Alignment Standard v0.3 format.

## Export as a Pandas DataFrame

`VerseData.dataframe()` produces an alignment matrix with source tokens as rows and (non-excluded) target tokens as columns:

```python
vd = mgr["41004003"]
df = vd.dataframe(hitmark="✓", missmark="")

# Display in a notebook
display(df)

# Export to CSV
df.to_csv("mark-4-3-alignments.csv")
```

## Export Alignment Pairs for a Verse Range

```python
import csv
from biblealignlib.burrito.util import filter_by_bcv

# Collect all pairs for Romans (book 45)
rows = []
for bcvid in mgr:
    if bcvid.startswith("45"):           # Romans
        vd = mgr[bcvid]
        for src, tgt in vd.get_pairs():
            rows.append({
                "bcv": bcvid,
                "src_id": src.id,
                "src_text": src.text,
                "src_lemma": src.lemma,
                "tgt_id": tgt.id,
                "tgt_text": tgt.text,
            })

with open("romans-pairs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
```

## Write Target Tokens as TSV

```python
from biblealignlib.burrito import TargetReader
from pathlib import Path

tr = TargetReader(alset.targetpath)

TargetReader.write_tsv(
    tokenlist=list(tr.values()),
    outpath=Path("targets-out.tsv"),
    fields=("id", "text", "source_verse", "skip_space_after", "exclude"),
)
```

## Filter by Book Before Exporting

```python
# Keep only Matthew (40) and Mark (41)
filtered_group = mgr.alignmentsreader.filter_books(keep=("40", "41"))

with open("gospels-partial.json", "w") as f:
    write_alignment_group(filtered_group, f)
```

## Add Records to an Existing Group

Use `Merger.add_records()` to append new records to an existing `AlignmentGroup` without duplicates:

```python
from biblealignlib.util.merger import Merger

merger = Merger(mgr1, mgr2)
new_records = (rec1, rec2, rec3)   # AlignmentRecord instances
extended_group = merger.add_records(mgr1.alignmentsreader.alignmentgroup, new_records)

with open("extended.json", "w") as f:
    write_alignment_group(extended_group, f)
```
