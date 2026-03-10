# The Alignment Model

## What Is a Word Alignment?

A word alignment links one or more tokens in a source text (Hebrew or Greek manuscript) to one or more tokens in a target translation. The goal is to identify which target words express the same meaning as which source words.

Alignments are inherently **many-to-many**: a single Greek word may translate to a phrase in English, and a phrase in Greek may collapse to a single English word. An alignment group captures this by holding *lists* of source and target tokens, not single tokens.

```
Source (Greek):     [ἐξῆλθεν] [ὁ] [σπείρων]
Target (English):   [A sower] [went out]

Alignment 1: [ἐξῆλθεν] ↔ [went out]
Alignment 2: [ὁ, σπείρων] ↔ [A sower]
```

## The Three Layers of Data

`biblealignlib` works with three kinds of data simultaneously:

**Source tokens** (`Source`)
: Individual words or morphemes in the source manuscript (SBLGNT, WLC, etc.). Each carries linguistic metadata: lemma, morphology, part of speech, Strong's number, and glosses.

**Target tokens** (`Target`)
: Individual words in the translation. Each tracks whether it is excluded from alignment (e.g. punctuation), whether it is required to be aligned, and its corresponding source verse (for versification mapping).

**Alignment records** (`AlignmentRecord`)
: Pairings of source and target token ID lists, with metadata (who created it, when, what status it is in, what type of alignment it represents).

## AlignmentRecord Structure

An `AlignmentRecord` does not store token objects — it stores **token IDs** wrapped in `AlignmentReference` containers:

```
AlignmentRecord
├── meta (Metadata)
│   ├── id        string identifier
│   ├── origin    "manual" | "eflomal" | "fast_align" | …
│   ├── status    "created" | "inProgress" | "reviewed" | "finalized"
│   ├── creator   name of person or tool
│   ├── note      free text annotation
│   └── created   timestamp
├── references
│   ├── "source" → AlignmentReference
│   │   ├── document  (Document: id="SBLGNT", scheme="BCVWP")
│   │   └── selectors ["41004003001", "41004003002", …]
│   └── "target" → AlignmentReference
│       ├── document  (Document: id="BSB", scheme="BCVW")
│       └── selectors ["41004003005", …]
└── type (TranslationType)
```

The indirection through IDs means that the same alignment group can be used across different token sets, and records can be serialized to JSON without embedding full token data.

## The AlignmentGroup

All records for a given source/target pair are bundled in an `AlignmentGroup`:

```
AlignmentGroup
├── documents  (source Document, target Document)
├── meta       (group-level Metadata)
├── roles      ("source", "target")
└── records    [AlignmentRecord, AlignmentRecord, …]
```

A group corresponds to one JSON file on disk. `write_alignment_group()` serializes it; `AlignmentsReader` reads it back.

## AlignmentTypes

Each record has a **type** that categorizes the semantic relationship between source and target:

- `TranslationType` — the default: the target word(s) directly translate the source word(s)
- `DirectedType` — a directional relationship (one-way)
- `AnaphoraType` — the target refers back to something expressed by the source
- Other types for morphological, formulaic, and untranslated items

In practice, most records use `TranslationType`.

## VerseData: The Working View

While `AlignmentRecord` is the storage format, day-to-day work uses `VerseData` — a per-verse container that joins token objects with their records:

```
VerseData (for BCV "41004003")
├── sources          [Source, Source, …]   — all source tokens in verse
├── targets          [Target, Target, …]   — all target tokens in verse
├── targets_included [Target, …]           — non-excluded targets only
├── alignments       [([src…], [tgt…]), …] — resolved token objects
└── records          (AlignmentRecord, …)  — original records
```

`Manager` builds `VerseData` objects on demand from the raw token dicts and alignment group. The `alignments` list is the most convenient form: each entry is a pair of resolved token lists ready for display or analysis.

## Excluded and Required Flags

Target tokens have two alignment control flags:

**`exclude`** — this token should not be aligned. Typically set on punctuation, articles that have no Greek equivalent, or filler words. Excluded tokens are omitted from `targets_included` and `unaligned_targets`.

**`required`** — this token *must* be aligned. Used to flag words that translators want to ensure are covered. Also available on source tokens.

## What "Manual" vs "Auto" Alignments Mean

The `AlignmentSet.alternateid` field distinguishes different versions of alignments for the same source/target pair:

- `"manual"` — human-curated alignments, the gold standard
- `"auto"` or a tool name (e.g. `"eflomal"`) — output from an automated aligner
- A person's name (e.g. `"Sunil"`) — one contributor's work, before merging

The `autoalign` package contains tools for running automated aligners and scoring their output against the manual gold standard. See [Score Alignments Against a Reference](../how-to/score-alignments.md).

## Data Integrity and Bad Records

When loading, `Manager` validates each record and removes those that are malformed. Common problems include:

- Source or target selector lists that are empty
- Token IDs that don't exist in the loaded token set
- A target token marked `exclude=True` being aligned anyway
- The same source token appearing in multiple records (duplicate)

These are tracked as `BadRecord` instances accessible via `mgr.alignmentsreader.badrecords`. Understanding which records are bad and why is important when curating or importing alignment data from external tools.
