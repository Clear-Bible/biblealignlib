# Scripture Burrito Alignment Format

`biblealignlib` implements the [Scripture Burrito Alignment Standard v0.3](https://docs.google.com/document/d/1zR5gsrm3gIoNiHVBlWz5_BBw3N-Ew1-4M5rMsFrPzSw/). This article explains what that means and how the library maps to it.

## What Is Scripture Burrito?

Scripture Burrito is an open standard for packaging and exchanging Bible-related data. The alignment flavor of the standard defines a JSON format for word-level alignments between two Bible texts.

The key design decisions of the standard:

1. **Roles** — each document in an alignment is identified by a named role (`"source"`, `"target"`), making the directionality explicit.
2. **Selectors** — alignments reference tokens by ID string, not by embedding token content. This keeps alignment files decoupled from the texts themselves.
3. **Metadata per record** — every alignment record carries its own provenance (who created it, when, and with what status).
4. **Document scheme** — each side specifies the ID scheme it uses (`"BCVWP"` for source manuscripts, `"BCVW"` for targets).

## File Layout

On disk, a Scripture Burrito alignment file is a JSON document structured as:

```json
{
  "meta": {
    "conformsTo": "0.3.1",
    "creator": "Clear Bible, Inc.",
    "created": "2024-01-15T10:00:00",
    "license": "CC BY 4.0"
  },
  "type": {
    "name": "wordAlignment"
  },
  "documents": [
    {"id": "SBLGNT", "scheme": "BCVWP", "role": "source"},
    {"id": "BSB",    "scheme": "BCVW",  "role": "target"}
  ],
  "records": [
    {
      "meta": {
        "id": "abc123",
        "origin": "manual",
        "status": "reviewed",
        "creator": "J. Smith",
        "created": "2024-01-10T14:30:00"
      },
      "source": {"selectors": ["n41004003001"]},
      "target": {"selectors": ["41004003002"]}
    }
  ]
}
```

Note that source selectors use Macula-prefixed IDs (`n` for NT, `o` for OT), while target selectors use bare IDs. `biblealignlib` handles this conversion automatically when reading and writing.

## How biblealignlib Maps to the Standard

| Standard concept | biblealignlib class |
|-----------------|---------------------|
| The full JSON file | `AlignmentGroup` |
| Top-level `meta` | `AlignmentGroup.meta` (a `Metadata` instance) |
| `documents` entry | `Document` dataclass |
| `records` entry | `AlignmentRecord` |
| Per-record `meta` | `AlignmentRecord.meta` (a `Metadata` instance) |
| `source`/`target` selectors | `AlignmentReference.selectors` |

`write_alignment_group()` serializes an `AlignmentGroup` to this format. `AlignmentsReader` deserializes it back.

## Alignment Types

The standard allows each record to carry a type describing the nature of the alignment. `biblealignlib` models these as subclasses of a base type class:

- `TranslationType` — direct translation correspondence (most records)
- `DirectedType` — one-way relationship
- `AnaphoraType` — anaphoric reference
- Others for morphological splits, formulaic expressions, and untranslated items

All records in a single `AlignmentGroup` must share the same type. Mixed-type datasets require separate groups.

## Versification

The standard does not prescribe how to handle versification differences between source and target. `biblealignlib`'s convention is to store the **source BCV** in the target token's `source_verse` attribute, and to use this (rather than the target's own BCV) when assigning target tokens to verses in `Manager`. This means the alignment records are always keyed to source verse references.

## Relation to the Macula Data Project

Clear Bible's alignment data is part of the broader Macula project, which provides linguistic annotations for Biblical manuscripts. The Macula ID scheme (the `n`/`o` prefix system) is a Macula convention layered on top of the BCVWP scheme. `biblealignlib` is aware of this convention but strips prefixes internally, adding them back only at serialization time.
