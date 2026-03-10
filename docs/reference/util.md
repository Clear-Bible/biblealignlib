# Reference: util

The `util` package provides utilities for comparing and merging alignment sets, and for vocabulary analysis.

---

## BCVPair

`biblealignlib.util.BCVPair`

Dataclass pairing the `VerseData` (if any) from two managers for a single BCV verse.

```python
from biblealignlib.util import BCVPair

pair = BCVPair(bcv="41004003", mgr1_data=vd1, mgr2_data=vd2)
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `bcv` | `str` | Verse identifier |
| `mgr1_data` | `Optional[VerseData]` | Data from first manager (or `None`) |
| `mgr2_data` | `Optional[VerseData]` | Data from second manager (or `None`) |
| `pairing` | `str` | Set in `__post_init__` (see below) |
| `diffs` | `Optional[list[DiffRecord]]` | Differences when both sides present |

**`pairing` values:**

| Value | Condition |
|-------|-----------|
| `"both"` | Both `mgr1_data` and `mgr2_data` are present |
| `"mgr1"` | Only `mgr1_data` is present |
| `"mgr2"` | Only `mgr2_data` is present |
| `"neither"` | Both are `None` |

When `pairing == "both"`, `diffs` is populated by calling `mgr1_data.diff(mgr2_data)`.

---

## Merger

`biblealignlib.util.merger.Merger`

Compares two `Manager` instances covering the same source, language, and target, and supports safe merging.

```python
from biblealignlib.util.merger import Merger

merger = Merger(mgr1, mgr2)
```

**Constructor:**

```python
Merger(mgr1: Manager, mgr2: Manager)
```

Both managers must have the same `sourceid`, `targetlanguage`, and `targetid` on their `AlignmentSet`.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `mgr1` | `Manager` | First manager |
| `mgr2` | `Manager` | Second manager |
| `allsrcbcv` | `list[str]` | All source BCV identifiers (from `mgr1`) |
| `bcv_pairs` | `dict[str, BCVPair]` | One entry per source BCV |
| `pairingcounts` | `Counter[str]` | Count of each pairing category |
| `overlaps` | `list[BCVPair]` | Pairs where `pairing == "both"` |
| `diffpairs` | `list[BCVPair]` | Overlaps with non-empty `diffs` |

**Methods:**

### `get_bcv_pairs() → dict[str, BCVPair]`

Builds the `bcv_pairs` dictionary. Called during `__init__`; not normally called directly.

---

### `show_diffs() → None`

Prints a summary of overlapping verses that have differences, grouped by book-chapter.

---

### `safe_merge(verbose=True) → AlignmentGroup`

Returns a new `AlignmentGroup` combining records where there is no conflict:

- Verses only in `mgr1` → taken from `mgr1`
- Verses only in `mgr2` → taken from `mgr2`
- Verses in both with no diffs → taken from `mgr1`
- Verses in both *with* diffs → **excluded** (require manual resolution)

```python
merged = merger.safe_merge(verbose=False)
```

---

### `add_records(algroup, records) → AlignmentGroup`

Add a tuple of `AlignmentRecord` instances to an existing `AlignmentGroup`. Raises `AssertionError` if any record duplicates an existing source selector.

```python
extended = merger.add_records(algroup, (rec1, rec2))
```

---

### `write_merge() → None`

Write the `safe_merge()` result to disk. Output filename combines both `alternateid` values:
`{sourceid}-{targetid}-{alt1}{alt2}.json`

---

## LemmaSetMaximizer

`biblealignlib.util.vocab.LemmaSetMaximizer`

Selects chapters in order of how much new vocabulary they contribute to a cumulative seen-lemma set, using a greedy algorithm. Useful for determining an efficient chapter ordering for alignment prioritization.

```python
from biblealignlib.util.vocab import LemmaSetMaximizer

lsm = LemmaSetMaximizer(SOURCES / "SBLGNT.tsv")
```

**Constructor:**

```python
LemmaSetMaximizer(sourcepath: Path)
```

`sourcepath` must be a path to a source TSV file (e.g. `SBLGNT.tsv`).

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `sourceitems` | `SourceReader` | All loaded source tokens |
| `bcids` | `dict[str, list[str]]` | Token IDs grouped by book-chapter ID |
| `doc_lemmas` | `dict[str, set[str]]` | Set of lemmas for each book-chapter |
| `gcm` | `list[tuple[str, set[str]]]` | Greedy chapter ordering result |

**`gcm` format:** A list of `(bcid, new_lemmas_set)` tuples in the order chapters were selected, where each `new_lemmas_set` contains only the lemmas that were *new* at the time that chapter was selected.

**Methods:**

### `greedy_vocab_maximization(doc_lemmas) → list[tuple[str, set[str]]]`

Runs the greedy selection algorithm. Called during `__init__`; not normally called directly.

---

### `write_vocab(output_path: Path) → None`

Write the GCM results to a TSV file with columns:

| Column | Description |
|--------|-------------|
| `BCID` | Book-chapter identifier |
| `BID` | Book identifier (2 digits) |
| `chapters` | Count of chapters selected from this book so far |
| `new_vocab` | Number of new lemmas contributed by this chapter |
