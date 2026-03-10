# Your First Alignment

This tutorial walks you through loading alignment data and exploring it verse by verse. By the end, you will have a working `Manager` instance, know how to navigate to a verse, and understand the structure of an alignment.

**Prerequisites:**

- Python 3.10 or later
- Access to the [Clear-Bible/Alignments](https://github.com/Clear-Bible/Alignments) repository data

---

## Step 1 — Install biblealignlib

```bash
pip install biblealignlib
```

Or with Poetry:

```bash
poetry add biblealignlib
```

---

## Step 2 — Configure Your Environment

`biblealignlib` needs to know where your Clear-Bible data repositories live. Create a `.env` file in your project root (or set the environment variable directly):

```bash
# .env
CLEARROOT=/path/to/your/Clear-Bible
```

The library expects this layout under `CLEARROOT`:

```
Clear-Bible/
├── Alignments/
│   └── data/
│       ├── sources/          ← Greek and Hebrew TSV files
│       └── eng/              ← English alignment data
│           ├── targets/
│           └── alignments/
└── alignments-eng/           ← Language-specific working data
    └── data/
```

You can verify that your paths are configured correctly:

```python
from biblealignlib import CLEARROOT, SOURCES

assert CLEARROOT.exists(), f"CLEARROOT not found: {CLEARROOT}"
assert SOURCES.exists(), f"SOURCES not found: {SOURCES}"
print(f"Data root: {CLEARROOT}")
print(f"Sources:   {SOURCES}")
```

---

## Step 3 — Create an AlignmentSet

An `AlignmentSet` describes the source manuscript, target translation, and language data you want to work with. Let's use the Greek New Testament (SBLGNT) aligned to the Berean Study Bible (BSB):

```python
from biblealignlib.burrito import AlignmentSet, CLEARROOT

alset = AlignmentSet(
    sourceid="SBLGNT",          # Greek New Testament
    targetid="BSB",              # Berean Study Bible
    targetlanguage="eng",        # ISO 639-3 language code
    langdatapath=CLEARROOT / "Alignments/data/eng",
    alternateid="manual",        # The curated manual alignments
)

print(alset.identifier)         # "SBLGNT-BSB-manual"
print(alset.canon)              # "nt"
```

The `AlignmentSet` does not load any data yet — it just knows *where* to find it.

---

## Step 4 — Load the Data with Manager

`Manager` reads all source tokens, target tokens, and alignment records from the files described by your `AlignmentSet`. It acts as a dictionary mapping BCV verse identifiers to `VerseData` instances.

```python
from biblealignlib.burrito import Manager

mgr = Manager(alset)

print(f"Source tokens loaded: {len(mgr.sourceitems)}")
print(f"Target tokens loaded: {len(mgr.targetitems)}")
print(f"Verses with alignments: {len(mgr)}")
```

Loading takes a few seconds the first time. The entire dataset is held in memory.

---

## Step 5 — Navigate to a Verse

BCV identifiers are zero-padded 8-digit strings: two digits for book, three for chapter, three for verse. Book numbering follows the standard Protestant canon (Matthew = 40, Mark = 41, etc.).

```python
# Mark 4:3 = book 41, chapter 004, verse 003
vd = mgr["41004003"]

print(repr(vd))                 # <VerseData: 41004003>
print(f"Source tokens: {len(vd.sources)}")
print(f"Target tokens: {len(vd.targets)}")
print(f"Alignments:    {len(vd.alignments)}")
```

---

## Step 6 — Explore the Alignments

Each alignment is a pair of lists: `([source tokens], [target tokens])`. Let's display them:

```python
# Print a tab-separated alignment table
vd.table()
# Example output:
# Ἀκούετε    Listen
# ἰδοὺ        !
# ἐξῆλθεν    A sower
# ὁ
# σπείρων
# σπεῖραι    went out    to sow
```

To see individual source tokens and their metadata:

```python
for src in vd.sources:
    print(f"{src.id}  {src.text:20}  {src.lemma:20}  {src.gloss}")
```

To see the alignment pairs as `(Source, Target)` tuples:

```python
for src, tgt in vd.get_pairs():
    print(f"{src.text} → {tgt.text}")
```

---

## Step 7 — Look at a Specific Source Token

Source tokens carry rich linguistic metadata:

```python
# Get the first word of Mark 4:3 directly
token = mgr.sourceitems["41004003001"]

print(token.text)     # "Ἀκούετε"
print(token.lemma)    # "ἀκούω"
print(token.pos)      # "verb"
print(token.strong)   # "G0191"
print(token.gloss)    # "Listen"
print(token.morph)    # morphological analysis string
```

---

## What You've Learned

- How to configure `CLEARROOT` so `biblealignlib` can find data files
- How to describe a dataset with `AlignmentSet`
- How to load all data with `Manager`
- How to navigate to a verse using its BCV identifier
- How to display and iterate over alignment pairs
- How to inspect individual source token metadata

## Next Steps

- **[How-to guides](../how-to/index.md)** — practical recipes for common tasks
- **[Explanation: The Alignment Model](../explanation/alignment-model.md)** — understand the conceptual structure
- **[Reference: burrito module](../reference/burrito.md)** — full API documentation
