# biblealignlib

`biblealignlib` is a Python library for managing word-level alignments between Bible source texts (Hebrew/Greek manuscripts) and target translations. It implements the [Scripture Burrito Alignment Standard v0.3](https://docs.google.com/document/d/1zR5gsrm3gIoNiHVBlWz5_BBw3N-Ew1-4M5rMsFrPzSw/) and supports both manual alignment curation and automated alignment verification.

## Documentation

This documentation follows the [Diátaxis framework](https://diataxis.fr/), organized into four sections by purpose:

| Section | Purpose | Start here when… |
|---------|---------|-------------------|
| [Tutorials](tutorials/index.md) | Learning-oriented | You're new to biblealignlib |
| [How-to guides](how-to/index.md) | Task-oriented | You need to accomplish a specific goal |
| [Reference](reference/index.md) | Information-oriented | You need to look up API details |
| [Explanation](explanation/index.md) | Understanding-oriented | You want to understand the concepts |

## Quick Start

```python
from biblealignlib.burrito import Manager, AlignmentSet, CLEARROOT

alset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "alignments-eng/data",
)
mgr = Manager(alset)

# Access verse data for Mark 4:3
vd = mgr["41004003"]
vd.table()
```

## Key Concepts

**source**
: The Hebrew or Greek source Bible text used for alignment. Common sources are `WLC` / `WLCM` (OT) and `SBLGNT` / `BGNT` (NT).

**target**
: The Bible translation being aligned to a source text (e.g. BSB, NIV, ESV).

**alignment**
: A group of source and target tokens that express equivalent content, stored as an `AlignmentRecord`.

**BCVWPID**
: The token identifier format: Book-Chapter-Verse-Word-Part ID (e.g. `41004003001` = Mark 4:3 word 1). See [Understanding BCVWPID Identifiers](explanation/bcvwpid.md).

## Data

Source and alignment data are in the [Clear-Bible/Alignments](https://github.com/Clear-Bible/Alignments) repository. See [Setting Up Your Environment](tutorials/first-alignment.md) for how to configure the library to find this data.

## Release Notes

See the [Release Notes](ReleaseNotes.md) for version history.
