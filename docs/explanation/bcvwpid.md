# Understanding BCVWPID Identifiers

Every token in `biblealignlib` is addressed by a **BCVWPID** identifier — a compact, zero-padded string encoding the book, chapter, verse, word position, and optionally a part index.

## Format

```
B B C C C V V V W W W P
│ │ └─┬─┘ └─┬─┘ └─┬─┘ └── Part (optional, 1 digit)
│ │   │     │     └────── Word (3 digits, 1-based)
│ │   │     └──────────── Verse (3 digits)
│ │   └────────────────── Chapter (3 digits)
└─┴────────────────────── Book (2 digits, standard Protestant canon)
```

Full form: 12 characters. Without part: 11 characters.

## Examples

| ID            | Reference              | Notes                     |
|---------------|------------------------|---------------------------|
| `40001001001` | Matthew 1:1, word 1    | No part index             |
| `41004003006` | Mark 4:3, word 6       |                           |
| `n41004003001`| Mark 4:3, word 1       | NT Macula prefix          |
| `o01001001001`| Genesis 1:1, word 1    | OT Macula prefix          |
| `40001001001` | Matthew 1:1, word 1, part 1 | With part index (subword)|

## Book Numbering

Book numbers follow the standard Protestant canon order:

- OT: Genesis = `01` … Malachi = `39`
- NT: Matthew = `40` … Revelation = `66`

The canon boundary at book 40 is important: source IDs for NT manuscripts carry the `n` Macula prefix, OT carry `o`.

## Macula Prefixes

The Macula project adds a single-character prefix to distinguish canons in mixed corpora:

- `n` — New Testament
- `o` — Old Testament

These prefixes appear in serialized JSON (Scripture Burrito format) but are stripped when tokens are loaded into memory. Use the utility functions to convert:

```python
from biblealignlib.burrito import macula_prefixer, macula_unprefixer, bare_id

# Add prefix (looks up the book number to determine OT/NT)
macula_prefixer("41004003001")    # → "n41004003001"
macula_prefixer("01001001001")    # → "o01001001001"

# Remove prefix
macula_unprefixer("n41004003001") # → "41004003001"

# bare_id strips any prefix (safe to call on already-bare IDs)
bare_id("n41004003001")           # → "41004003001"
bare_id("41004003001")            # → "41004003001"
```

## The BCV Subset

Alignment data is often grouped at the **verse** level, using just the first 8 characters: `BBCCCVVV`. This is called the BCV identifier.

```python
token = mgr.sourceitems["41004003001"]
print(token.bcv)       # "41004003"
print(token.bare_id)   # "41004003001"
```

`Manager` is keyed by BCV identifiers, so `mgr["41004003"]` returns the `VerseData` for that verse.

## Part Indices

The part (P) digit handles subword tokens — cases where a single written word in the source text is analyzed as more than one morpheme, each requiring independent alignment. This is more common in Hebrew than Greek. A part index of `0` (or absent) means the whole word.

## Versification

Target translations may divide verses differently from the source. When this happens, a target token's `source_verse` attribute will differ from its own `bcv`. For example, a token physically in the target's verse 3 may correspond to source verse 4 due to a versification shift.

```python
tgt = mgr.targetitems["44019041001"]
if not tgt.same_source_verse:
    print(f"Versification difference: target BCV {tgt.bcv}, source BCV {tgt.source_verse}")
```

`Manager` handles this transparently when building `VerseData`: target tokens are assigned to verses based on `source_verse`, not their own BCV.
