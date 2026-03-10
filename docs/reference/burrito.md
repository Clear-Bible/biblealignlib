# Reference: burrito

The `burrito` package is the core of `biblealignlib`. It provides token types, alignment data structures, readers, writers, and the `Manager` coordinator.

```python
from biblealignlib.burrito import (
    AlignmentGroup, AlignmentRecord, AlignmentReference,
    AlignmentSet, AlignmentsReader,
    BaseToken, Source, SourceReader,
    Target, TargetReader,
    Document, Metadata,
    Manager, VerseData,
    TranslationType,
    asbool, bare_id, macula_prefixer, macula_unprefixer,
    groupby_key, groupby_bcv, groupby_bcid, token_groupby_bc,
    filter_by_bcv,
    write_alignment_group,
    CLEARROOT, SOURCES,
)
```

---

## Constants

### `CLEARROOT`
`Path` — Root of the Clear-Bible data repositories, read from the `CLEARROOT` environment variable (or `.env` file). Defaults to `~/git/Clear-Bible`.

### `SOURCES`
`Path` — Path to source TSV files: `{CLEARROOT}/Alignments/data/sources`.

---

## Token Classes

### `BaseToken`

Base dataclass for all tokens.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | BCVWPID identifier (bare, no Macula prefix) |
| `text` | `str` | Surface form (may be empty for copyrighted texts) |
| `altId` | `str` | Alternate identifier |
| `aligned` | `bool` | Display flag |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `bcv` | `str` | First 8 characters of `id` (book+chapter+verse) |
| `bare_id` | `str` | `id` with any canon prefix stripped |
| `isempty` | `bool` | True if `text == ""` |

---

### `Source`

Extends `BaseToken`. Represents a source manuscript token (Greek or Hebrew).

| Attribute | Type | Description |
|-----------|------|-------------|
| `strong` | `str` | Strong's number (e.g. `"G0191"`) |
| `lemma` | `str` | Lemmatized form |
| `morph` | `str` | Morphological analysis string |
| `gloss` | `str` | Primary English gloss |
| `gloss2` | `str` | Secondary gloss (alternate language) |
| `pos` | `str` | Part of speech: `"noun"`, `"verb"`, `"adj"`, `"adv"`, `"det"`, `"pron"`, `"prep"`, `"conj"`, `"part"`, `"intj"` |
| `required` | `bool` | Must be aligned |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_content` | `bool` | True for noun, verb, adj, adv |
| `maculaid` | `str` | ID with Macula `n`/`o` prefix |

**Methods:**

- `asdict(omittext=False, essential=False) → dict` — serialize to dictionary

---

### `SourceReader`

`UserDict[str, Source]` — loads a source TSV file.

```python
sr = SourceReader(SOURCES / "SBLGNT.tsv")
token = sr["41004003001"]
```

**Methods:**

- `vocabulary(tokenattr="lemma", lower=True) → set[str]`
- `term_tokens(term, tokenattr="lemma", lowercase=True) → list[Source]`
- `book_token_counts() → Counter[str]`
- `book_type_counts(tokenattr="lemma") → dict[str, int]`

---

### `Target`

Extends `BaseToken`. Represents a target translation token.

| Attribute | Type | Description |
|-----------|------|-------------|
| `source_verse` | `str` | BCV of the *source* verse this token corresponds to |
| `exclude` | `bool` | Token is ineligible for alignment |
| `required` | `bool` | Token must be aligned |
| `skip_space_after` | `bool` | No space after this token in display |
| `isPunc` | `bool` | Token is punctuation |
| `isPrimary` | `bool` | Primary token for multi-word alignment display |
| `transType` | `str` | Translation type annotation |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `same_source_verse` | `bool` | True if `source_verse == bcv` |

**Methods:**

- `asdict(fields=None, omitfalse=False) → dict`

---

### `TargetReader`

`UserDict[str, Target]` — loads a target TSV file.

```python
tr = TargetReader(langdatapath / "targets/BSB/nt_BSB.tsv")
token = tr["41004003002"]
```

**Constructor parameters:**

- `tsvpath: Path`
- `detect_punc: bool = False` — auto-detect punctuation tokens

**Methods:**

- `term_tokens(term, tokenattr="text", lowercase=True) → list[Target]`
- `get_source_bcvs() → dict[str, str]` — map target BCV → source BCV
- `write_tsv(tokenlist, outpath, fields, excludefn=None) → None` (classmethod)

---

## Alignment Data Structures

### `Document`

Dataclass identifying a text corpus in an alignment.

| Field | Type | Description |
|-------|------|-------------|
| `docid` | `str` | Corpus identifier (e.g. `"SBLGNT"`, `"BSB"`) |
| `scheme` | `str` | ID scheme (`"BCVWP"` for source, `"BCVW"` for target) |

---

### `Metadata`

Dataclass for provenance information (used at both group and record level).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `str` | `""` | Record identifier |
| `origin` | `str` | `""` | How it was created (`"manual"`, `"eflomal"`, …) |
| `status` | `str` | `"created"` | Workflow status |
| `creator` | `str` | `""` | Author or tool name |
| `note` | `str` | `""` | Free-form annotation |
| `created` | `str` | `""` | ISO timestamp |
| `conformsTo` | `str` | `"0.3.1"` | Standard version |

---

### `AlignmentReference`

Wraps a list of token IDs for one side of an alignment.

| Attribute | Type | Description |
|-----------|------|-------------|
| `document` | `Document` | Which corpus these IDs come from |
| `selectors` | `list[str]` | Token ID strings |

**Property:**

- `incomplete: bool` — True if any selector is `"MISSING"`

---

### `AlignmentRecord`

Single word/phrase alignment.

| Attribute | Type | Description |
|-----------|------|-------------|
| `meta` | `Metadata` | Record-level provenance |
| `references` | `dict[str, AlignmentReference]` | Keyed by role name |
| `type` | alignment type | Usually `TranslationType` |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `identifier` | `str` | `meta.id` |
| `source_selectors` | `list[str]` | Selectors from the `"source"` reference |
| `target_selectors` | `list[str]` | Selectors from the `"target"` reference |
| `source_bcv` | `str` | BCV extracted from first source selector |
| `target_bcv` | `str` | BCV extracted from first target selector |
| `incomplete` | `bool` | Any reference has `MISSING` selectors |

**Methods:**

- `asdict(positional=False, withmeta=True, withmaculaprefix=True) → dict`

---

### `AlignmentGroup`

Top-level container for all records in a source/target pair.

| Attribute | Type | Description |
|-----------|------|-------------|
| `documents` | `tuple[Document, Document]` | (source, target) |
| `meta` | `Metadata` | Group-level provenance |
| `records` | `list[AlignmentRecord]` | All alignment records |
| `roles` | `tuple[str, str]` | Usually `("source", "target")` |

**Properties:**

- `canon: str` — `"ot"` or `"nt"`, inferred from source document ID

**Methods:**

- `verserecords() → dict[str, list[AlignmentRecord]]` — group records by BCV
- `asdict(hoist=True) → dict` — serialize for JSON output

---

### `write_alignment_group`

```python
write_alignment_group(group: AlignmentGroup, fp: IO[str]) → None
```

Serialize an `AlignmentGroup` to a file object in Scripture Burrito JSON format.

---

### `AlignmentsReader`

Reads a Scripture Burrito JSON file and provides access to the resulting `AlignmentGroup`.

```python
reader = AlignmentsReader(alset.alignmentpath)
group = reader.alignmentgroup
```

**Attributes:**

- `alignmentgroup: AlignmentGroup`
- `badrecords: dict[str, list[BadRecord]]` — records removed during validation

**Methods:**

- `filter_books(keep: tuple[str, ...]) → AlignmentGroup`

---

## AlignmentSet

Configuration for a dataset (paths + IDs). Does not load data.

```python
AlignmentSet(
    sourceid: str,
    targetid: str,
    targetlanguage: str,
    langdatapath: Path,
    alternateid: str = "",
)
```

**Computed properties:**

| Property | Description |
|----------|-------------|
| `identifier` | `"{sourceid}-{targetid}-{alternateid}"` |
| `canon` | `"ot"` or `"nt"` based on `sourceid` |
| `sourcepath` | Path to source TSV |
| `targetpath` | Path to target TSV |
| `alignmentpath` | Path to alignment JSON |

**Methods:**

- `check_files() → None` — raise `FileNotFoundError` if any file is missing

---

## Manager

`UserDict[str, VerseData]` — loads and coordinates all data for an `AlignmentSet`.

```python
mgr = Manager(alset)
vd = mgr["41004003"]   # Mark 4:3
```

**Constructor:**

```python
Manager(alignmentset: AlignmentSet, keepbadrecords: bool = False)
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `alignmentset` | `AlignmentSet` | The configuration used |
| `sourceitems` | `SourceReader` | All source tokens |
| `targetitems` | `TargetReader` | All target tokens |
| `alignmentsreader` | `AlignmentsReader` | All alignment records |
| `bcv` | `dict` | Organized data by BCV key |

**Methods:**

- `token_alignments(term, role="source", tokenattr="text", lowercase=True) → list[AlignmentRecord]`
- `display_record(record: AlignmentRecord) → str`
- `get_source_targets(source: Source) → list[Target]`

---

## VerseData

Per-verse view of alignments. Created by `Manager.__getitem__()`.

```python
@dataclass
class VerseData:
    bcvid: str
    alignments: list[tuple[list[Source], list[Target]]]
    sources: list[Source]
    targets: list[Target]
    records: tuple[AlignmentRecord, ...]
```

**Computed attributes (set in `__post_init__`):**

- `targets_included: tuple[Target, ...]` — non-excluded targets

**Properties:**

- `aligned_sources: list[Source]` — sources present in at least one alignment
- `unaligned_sources: list[Source]` — sources in no alignment
- `aligned_targets: list[Target]` — non-excluded targets in at least one alignment
- `unaligned_targets: list[Target]` — non-excluded targets in no alignment

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_pairs(essential=False)` | `list[tuple[Source, Target]]` | Flattened alignment pairs; `essential=True` limits to content words |
| `get_texts(typeattr="targets", unique=False, keepexcluded=False)` | `list[str]` | Text strings from tokens |
| `get_source_targets()` | `dict[Source, list[Target]]` | Map each source to its aligned targets |
| `get_source_alignments(source)` | `list[Target]` | Targets aligned to a specific source token |
| `table(aligned=True, srcwidth=30)` | (prints) | Tab-separated display |
| `dataframe(hitmark="X", missmark=" ")` | `pd.DataFrame` | Alignment hit matrix |
| `diff(other: VerseData)` | `list[DiffRecord]` | Differences between two VerseData instances |
| `unaligned(typeattr, keepexcluded=False)` | (prints) | Display unaligned tokens |

---

## BadRecord

Tracks malformed alignment records detected during loading.

```python
from biblealignlib.burrito.BadRecord import Reason, BadRecord
```

**`Reason` enum values:**

| Value | Meaning |
|-------|---------|
| `NOSOURCE` | Source selectors list is empty |
| `NOTARGET` | Target selectors list is empty |
| `EMPTYSOURCE` | Source selector is an empty string |
| `EMPTYTARGET` | Target selector is an empty string |
| `DUPLICATESOURCE` | Source token appears in multiple records |
| `DUPLICATETARGET` | Target token appears in multiple records |
| `MISSINGSOURCE` | Source token ID not in `sourceitems` |
| `MISSINGTARGETSOME` | Some target IDs not in `targetitems` |
| `MISSINGTARGETALL` | All target IDs not in `targetitems` |
| `ALIGNEDEXCLUDE` | Aligned token has `exclude=True` |
| `UNKNOWN` | Uncategorized error |

---

## Utility Functions

### Grouping

```python
from biblealignlib.burrito import groupby_key, groupby_bcv, groupby_bcid, token_groupby_bc

groupby_key(items, key)          # dict[key, list[item]]
groupby_bcv(tokens)              # dict[bcv_str, list[Token]]
groupby_bcid(id_list)            # dict[bcid_str, list[str]]
token_groupby_bc(tokens)         # dict[bc_str, list[Token]]
```

### Filtering

```python
from biblealignlib.burrito import filter_by_bcv

filter_by_bcv(items, startbcv, endbcv, key=lambda x: x.bcv)
```

### ID Conversion

```python
from biblealignlib.burrito import macula_prefixer, macula_unprefixer, bare_id

macula_prefixer("41004003001")    # → "n41004003001"
macula_unprefixer("n41004003001") # → "41004003001"
bare_id("n41004003001")           # → "41004003001"
```

### Boolean Serialization

```python
from biblealignlib.burrito import asbool
asbool(True)    # → "y"
asbool(False)   # → "n"
```
