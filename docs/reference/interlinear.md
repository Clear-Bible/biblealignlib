# Reference: interlinear

The `interlinear` package generates interlinear and reverse-interlinear display data.

---

## token.py — AlignedToken

```python
from biblealignlib.interlinear.token import AlignedToken
```

### `AlignedToken`

Dataclass wrapping a source/target token pair for interlinear display.

**Constructor:**

```python
AlignedToken(
    targettoken: Optional[Target] = None,
    sourcetoken: Optional[Source] = None,
    aligned: bool = False,
)
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `display()` | `str` | `"(target_id source_id)"` formatted string |
| `ids()` | `str` | `"source_id target_id"` |
| `asdict()` | `dict[str, str]` | Serializable dict with renamed keys (`targetid`, `sourceid`, etc.) |
| `__lt__(other)` | `bool` | Sort by target ID then source ID |

Supports `None` for either token to represent unaligned tokens (target with no source, or source with no target).

---

## reverse.py — Reverse Interlinear

```python
from biblealignlib.interlinear.reverse import Reader, Writer
```

### `Reader`

`UserList[AlignedToken]` — reads a `Manager` and produces a sorted list of aligned tokens suitable for reverse interlinear output.

**Constructor:**

```python
Reader(
    mgr: Manager,
    exclude: bool = False,   # if True, include excluded target tokens
)
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `aligned_tokens` | `list[AlignedToken]` | All tokens, sorted by target then source ID |
| `included_targets` | `list[Target]` | Target tokens present in output |
| `target_alignments` | `dict[Target, list[list[Source]]]` | Mapping from target to aligned source groups |

The list itself (`self`) contains the `AlignedToken` instances in sorted order.

---

### `Writer`

Writes a reverse interlinear TSV file from a `Reader`.

**Constructor:**

```python
Writer(reader: Reader)
```

**Attributes:**

- `fieldnames: list[str]` — TSV column names:
  `targetid`, `targettext`, `source_verse`, `skip_space_after`, `exclude`, `sourceid`, `sourcetext`, `altId`, `strongs`, `gloss`, `gloss2`, `lemma`, `pos`, `morph`, `required`

**Methods:**

### `write(outpath: Path) → None`

Write one TSV row per aligned target token to `outpath`. Each row contains fields from both the target and source tokens.

**Usage:**

```python
from biblealignlib.interlinear.reverse import Reader, Writer

reader = Reader(mgr, exclude=False)
writer = Writer(reader)
writer.write(Path("output/reverse-interlinear.tsv"))
```
