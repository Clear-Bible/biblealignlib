# Reference: autoalign

The `autoalign` package supports automated alignment generation, pharaoh-format conversion, and scoring against a gold-standard reference.

---

## Score.py — Metrics Dataclasses

```python
from biblealignlib.autoalign.Score import VerseScore, GroupScore, EssentialVerseScore
```

### `_BaseScore`

Abstract base dataclass providing metric computation. Not used directly.

**Computed fields (set by `compute_metrics()`):**

| Field | Type | Description |
|-------|------|-------------|
| `precision` | `float` | TP / (TP + FP) |
| `recall` | `float` | TP / (TP + FN) |
| `f1` | `float` | Harmonic mean of precision and recall |
| `aer` | `float` | Alignment Error Rate = 1 − precision |

**Methods:**

- `compute_metrics() → None` — calculate precision, recall, F1, AER from hit counts
- `summary(width=4, brief=True) → str` — formatted one-line string
- `summary_dict(width=4) → dict[str, str]` — `{"AER": …, "F1": …, "Precision": …, "Recall": …}`
- `asdict(ndigits=3) → dict[str, Any]` — DataFrame-compatible row

---

### `VerseScore`

```python
VerseScore(
    identifier: str = "",
    reference: Optional[VerseData] = None,
    hypothesis: Optional[VerseData] = None,
    true_positives: int = 0,
    false_positives: int = 0,
    false_negatives: int = 0,
)
```

Metrics for a single verse. `identifier` is typically the BCV string.

---

### `EssentialVerseScore`

Extends `VerseScore`. Restricts evaluation to content words (noun, verb, adj, adv) only.

---

### `GroupScore`

```python
GroupScore(
    identifier: str = "",
    verse_scores: list[VerseScore] = field(default_factory=list),
)
```

Aggregated metrics across multiple verses. `compute_metrics()` sums the hit counts from all `verse_scores` before computing ratios.

---

## scorer.py — Scoring Engine

```python
from biblealignlib.autoalign.scorer import Scorer, ScoreCondition
```

### `Scorer`

Extends `Manager`. Loads both a reference (gold-standard) and a hypothesis alignment set and compares them.

**Constructor:**

```python
Scorer(
    referenceset: AlignmentSet,
    hypothesispath: Path,
    hypothesisaltid: str,
    creator: str = "GrapeCity",
)
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `score_verse(bcvid, essential=False)` | `Optional[VerseScore]` | Score a single verse |
| `score_group(identifier, essential=False)` | `GroupScore` | Score a named group of verses |
| `score_partial(startbcv, endbcv, essential=False)` | `GroupScore` | Score a verse range |
| `score_all(essential=False)` | `GroupScore` | Score all verses |
| `log_score(summary_dict, comment="")` | `None` | Append result to a log file |
| `verse_dataframe(bcv, truepos, falseneg, falsepos, trueneg, srcattr)` | `pd.DataFrame` | Alignment matrix with TP/FP/FN/TN markers |

**`verse_dataframe` parameters:**

- `truepos="R-H"` — marker for reference *and* hypothesis aligned (true positive)
- `falseneg="R--"` — reference aligned but hypothesis missed (false negative)
- `falsepos="--H"` — hypothesis aligned but not in reference (false positive)
- `trueneg="   "` — neither aligned (true negative)
- `srcattr="text"` — source token attribute to use as row labels

---

### `ScoreCondition`

Convenience subclass of `Scorer` that derives file paths from named parameters.

**Constructor:**

```python
ScoreCondition(
    targetlang: str,
    targetid: str,
    condition: str,           # used as hypothesisaltid and to locate the hypothesis path
    sourceid: str = "SBLGNT",
    hypothesisaltid: str = "eflomal",
)
```

Inherits all `Scorer` methods.

---

## mapper.py — Pharaoh Format Conversion

```python
from biblealignlib.autoalign.mapper import PharaohMapper
```

### `PharaohMapper`

Extends `Manager`. Converts Scripture Burrito alignment records to pharaoh-format index pairs for use with external alignment tools (eflomal, fast_align, etc.).

**Constructor:**

```python
PharaohMapper(
    alignmentset: AlignmentSet,
    origin: str = "manual",
    pipedname: str = "",
)
```

**Key attributes:**

- `source_bcvs: dict[str, list[Target]]` — maps source BCV to aligned target tokens
- `bcv["mappings"]: dict[str, CorpusMapping]` — per-verse corpus mapping objects

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `selector_indices(record, mapping, typeattr)` | `list[int]` | Pharaoh indices for a record's selectors |
| `record_pairs(record, mapping)` | `tuple[tuple[int, int], …]` | Cartesian product of source×target indices |
| `bcv_pharaoh(bcv)` | `tuple[tuple[int, int], …]` | All pharaoh pairs for a verse |
| `get_partial_mappings(startbcv, endbcv)` | `list[CorpusMapping]` | Filter mappings to a verse range |

---

## Related: PharaohWriter and PharaohReader

The `writer` and `reader` modules convert entire alignment sets to/from the "piped" pharaoh format used by external tools:

```python
from biblealignlib.autoalign.writer import PharaohWriter
from biblealignlib.autoalign.reader import PharaohReader

# Write piped format for external tool
pw = PharaohWriter(targetlang="eng", targetid="BSB", sourceid="SBLGNT")
pw.write_piped()

# Read back results
pr = PharaohReader(
    targetlang="eng",
    targetid="BSB",
    sourceid="SBLGNT",
    condition="20241220_eflomal_text",
)
alignment_group = pr.make_burrito()
```
