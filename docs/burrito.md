# Burrito Module Documentation

The `burrito` module provides the core infrastructure for working with Bible alignment data in Scripture Burrito format. It handles reading, writing, validating, and managing word-level alignments between source manuscripts (Hebrew/Greek) and target translations.

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Module Structure](#module-structure)
- [Key Classes](#key-classes)
- [Common Workflows](#common-workflows)
- [API Reference](#api-reference)

## Overview

The burrito module implements the [Scripture Burrito Alignment Standard v0.3](https://docs.google.com/document/d/1zR5gsrm3gIoNiHVBlWz5_BBw3N-Ew1-4M5rMsFrPzSw/), providing:

- **Token Management**: Source (manuscript) and target (translation) token representations
- **Alignment Records**: Structured data linking source and target tokens
- **Data Validation**: Detection and reporting of malformed alignment data
- **I/O Operations**: Reading from TSV and JSON, writing to Scripture Burrito JSON format
- **Verse-level Access**: VerseData class for working with complete verse alignments

## Core Concepts

### BCVWPID Identifier Format

Token identifiers use the BCVWPID format: **Book-Chapter-Verse-Word-Part ID**

- **Format**: `BBCCCVVVWWWP` (12 characters, or 11 without part index)
- **Example**: `40001001001` = Matthew 1:1, word 1
- **Prefixed**: `n40001001001` (NT) or `o01001001001` (OT) - Macula format

```python
# BCVWPID components:
# BB    = Book (01-66, zero-padded)
# CCC   = Chapter (zero-padded)
# VVV   = Verse (zero-padded)
# WWW   = Word index (zero-padded)
# P     = Part index (optional, for subword tokens)
```

### Scripture Burrito Format

Alignment data is organized hierarchically:

```
AlignmentGroup
├── metadata (Metadata)
├── documents (tuple of Document)
├── roles (source, target)
└── records (list of AlignmentRecord)
    ├── meta (Metadata)
    ├── references (dict)
    │   ├── source (AlignmentReference)
    │   └── target (AlignmentReference)
    └── type (TranslationType)
```

### Data Flow

#### Reading Alignment Data
```
TSV Files → Readers → Token Objects → Manager → VerseData
  ├── sources/{sourceid}.tsv → SourceReader → Source tokens
  ├── targets/{targetid}/{canon}_{targetid}.tsv → TargetReader → Target tokens
  └── alignments/{targetid}/{sourceid}-{targetid}-{alt}.json → AlignmentsReader → AlignmentRecords
```

#### Writing Alignment Data
```
AlignmentGroup → write_alignment_group() → JSON file
```

## Module Structure

```
burrito/
├── __init__.py              # Public API exports
├── BaseToken.py             # Base class for Source and Target
├── source.py                # Source token management (manuscript)
├── target.py                # Target token management (translation)
├── AlignmentGroup.py        # Scripture Burrito data structures
├── AlignmentRecord.py       # Individual alignment records
├── AlignmentSet.py          # Configuration for alignment data sets
├── AlignmentType.py         # Type system (translation, related, etc.)
├── alignments.py            # Reading/writing alignment records
├── manager.py               # Manager: coordinates all data reading
├── VerseData.py             # Verse-level alignment container
├── BadRecord.py             # Error detection and reporting
└── util.py                  # Utility functions (grouping, filtering)
```

## Key Classes

### BaseToken

Base class for both `Source` and `Target` tokens.

**Key Attributes:**

- `id`: BCVWPID identifier
- `text`: Surface form of the word
- `altId`: Alternate identifier (often text with index)
- `aligned`: Boolean flag for display purposes
- `text_unique`: Variant text for disambiguation

**Key Properties:**

- `bcv`: BCV-format verse reference (e.g., "40001001")
- `bare_id`: ID without Macula prefix
- `isempty`: True if text is empty string

### Source

Represents a source manuscript token (Greek/Hebrew).

**Attributes:**

- All BaseToken attributes, plus:
- `strong`: Strong's number (normalized, e.g., "G0001")
- `gloss`: English gloss
- `gloss2`: Alternate language gloss
- `lemma`: Source language lemma
- `pos`: Part of speech (noun, verb, adj, adv, etc.)
- `morph`: Morphological information
- `required`: Whether token should be aligned

**Key Methods:**

```python
# Check if token is content-bearing
source.is_content  # True for noun, verb, adj, adv

# Get Macula-prefixed ID
source.maculaid  # Returns "n40001001001" or "o01001001001"

# Export as dictionary
source.asdict(omittext=False, essential=False)
```

**Example:**

```python
from biblealignlib.burrito import SourceReader, SOURCES

src = SourceReader(SOURCES / "SBLGNT.tsv")
token = src["40001001001"]  # Matthew 1:1, word 1
print(token.text)           # "Βίβλος"
print(token.lemma)          # "βίβλος"
print(token.gloss)          # "Book"
print(token.pos)            # "noun"
print(token.strong)         # "G0976"
```

### Target

Represents a target translation token.

**Attributes:**

- All BaseToken attributes, plus:
- `source_verse`: BCV of corresponding source verse
- `skip_space_after`: No space after this token in display
- `exclude`: Token should not be eligible for alignment
- `required`: Token should be aligned
- `transType`: Translation type marker
- `isPunc`: Is this token punctuation?
- `isPrimary`: Primary word for multi-word alignments

**Key Methods:**

```python
# Check if source verse matches token verse
target.same_source_verse  # False indicates versification differences

# Check if token is punctuation
target.ispunc_token

# Export as dictionary
target.asdict(fields=("id", "text", "exclude"), omitfalse=True)
```

**Example:**
```python
from biblealignlib.burrito import TargetReader, CLEARROOT

tr = TargetReader(CLEARROOT / "alignments-eng/data/targets/BSB/nt_BSB.tsv")
token = tr["40001001001"]
print(token.text)           # "book"
print(token.source_verse)   # "40001001"
print(token.exclude)        # False
print(token.isPunc)         # False
```

### AlignmentSet

Configuration for a set of alignment files.

**Attributes:**

- `sourceid`: Source manuscript ID (e.g., "SBLGNT", "OSHB")
- `targetid`: Target translation ID (e.g., "BSB", "NIV")
- `targetlanguage`: ISO 639-3 language code (e.g., "eng", "fra")
- `langdatapath`: Path to language-specific data directory
- `alternateid`: Alternate version ID (e.g., "manual", "auto")

**Computed Paths:**

- `sourcepath`: Path to source TSV file
- `targetpath`: Path to target TSV file
- `alignmentpath`: Path to alignment JSON file
- `tomlpath`: Path to TOML metadata file

**Example:**

```python
from biblealignlib.burrito import AlignmentSet, CLEARROOT

alset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "alignments-eng/data",
    alternateid="manual"
)

print(alset.identifier)      # "SBLGNT-BSB-manual"
print(alset.canon)           # "nt"
alset.check_files()          # Verify all files exist
```

### Manager

Coordinates reading of source, target, and alignment data. Acts as a dictionary mapping BCV identifiers to `VerseData` instances.

**Initialization:**

```python
from biblealignlib.burrito import Manager, AlignmentSet, CLEARROOT

alset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "alignments-eng/data"
)
mgr = Manager(alset)
```

**Key Attributes:**

- `sourceitems`: SourceReader with all source tokens
- `targetitems`: TargetReader with all target tokens
- `alignmentsreader`: AlignmentsReader with all alignment records
- `bcv`: Dict organizing data by BCV reference
- `data`: Dict mapping BCV → VerseData (same as `self`)

**Accessing Data:**

```python
# Get verse data
verse = mgr["40001001"]  # Returns VerseData for Matthew 1:1

# Search for alignments containing a term
records = mgr.token_alignments("Ἰησοῦς", role="source", tokenattr="text")

# Display a specific record
print(mgr.display_record(records[0]))
```

**Bad Records:**

The Manager automatically detects and reports malformed alignment records:

```python
# Access bad records found during data loading
bad = mgr.alignmentsreader.badrecords
# Dict: record_id → list of BadRecord instances

# Common reasons for bad records:
# - NOSOURCE: No source selectors
# - NOTARGET: No target selectors
# - DUPLICATESOURCE: Source token aligned multiple times
# - DUPLICATETARGET: Target token aligned multiple times
# - MISSINGSOURCE: Source token ID not found
# - MISSINGTARGET: Target token ID not found
# - ALIGNEDEXCLUDE: Excluded token is aligned
```

### VerseData

Manages alignments, sources, and targets for a single verse.

**Attributes:**

- `bcvid`: Verse identifier (e.g., "40001001")
- `alignments`: List of (sources, targets) tuple pairs
- `records`: Tuple of AlignmentRecord instances
- `sources`: List of Source tokens
- `targets`: List of Target tokens
- `targets_included`: Tuple of non-excluded Target tokens

**Key Methods:**

```python
# Get alignment pairs (flattened, with repetition)
pairs = verse.get_pairs(essential=False)
# Returns: [(Source, Target), (Source, Target), ...]

# With essential=True, only content words (noun, verb, adj, adv)
content_pairs = verse.get_pairs(essential=True)

# Display alignments
verse.display(termsonly=False)  # Full token details
verse.display(termsonly=True)   # Just text strings
verse.table()                    # Tab-separated table

# Get text lists
source_texts = verse.get_texts(typeattr="sources")
target_texts = verse.get_texts(typeattr="targets", keepexcluded=False)
unique_texts = verse.get_texts(typeattr="targets", unique=True)

# Create alignment matrix as pandas DataFrame
df = verse.dataframe(hitmark="X", missmark=" ")
```

**Example:**

```python
verse = mgr["40001001"]  # Matthew 1:1

# Explore the verse
print(f"Sources: {len(verse.sources)}")
print(f"Targets: {len(verse.targets)}")
print(f"Alignments: {len(verse.alignments)}")

# Display alignments
verse.table()
# Output:
# Βίβλος    book
# γενέσεως  of the genealogy

# Get alignment pairs
for src, trg in verse.get_pairs():
    print(f"{src.text} → {trg.text}")
```

### AlignmentGroup

Top-level container for a complete set of alignment records.

**Attributes:**

- `documents`: Tuple of (source Document, target Document)
- `meta`: Metadata for the group
- `records`: List of AlignmentRecord instances
- `roles`: Tuple of role names ("source", "target")
- `canon`: Canon identifier ("ot" or "nt")

**Methods:**

```python
# Export to dict for serialization
group_dict = group.asdict(hoist=True)

# Get verse-level records
verse_records = group.verserecords()
# Returns: dict mapping BCV → list of AlignmentRecords
```

**Writing to JSON:**

```python
from biblealignlib.burrito import write_alignment_group

with open("output.json", "w") as f:
    write_alignment_group(group, f)
```

### AlignmentRecord

Individual alignment linking source and target tokens.

**Attributes:**

- `meta`: Metadata instance (includes id, status, origin, note)
- `references`: Dict with keys "source" and "target"
  - Values are AlignmentReference instances
- `type`: TranslationType instance

**Key Properties:**

```python
record.identifier           # Record ID from metadata
record.source_selectors     # List of source token IDs
record.target_selectors     # List of target token IDs
record.source_bcv           # BCV of source verse
record.incomplete           # True if any selectors are "MISSING"
```

**Methods:**

```python
# Export as dictionary
rec_dict = record.asdict(
    positional=False,           # Use role names as keys
    withmeta=True,              # Include metadata
    withmaculaprefix=True       # Add 'n'/'o' prefix to source IDs
)
```

### Utility Functions

**Grouping Functions:**

```python
from biblealignlib.burrito import util

# Group tokens by BCV
bcv_dict = util.groupby_bcv(token_list)
# Returns: dict[str, list[Token]]

# Group by book-chapter only
bc_dict = util.token_groupby_bc(token_list)

# Group by arbitrary key
grouped = util.groupby_key(items, key=lambda x: x.some_attribute)
```

**Filtering:**

```python
# Filter items by BCV range
subset = util.filter_by_bcv(
    items,
    startbcv="40001001",
    endbcv="40002023",
    key=lambda item: item.bcv
)
```

**ID Manipulation:**

```python
from biblealignlib.burrito import macula_prefixer, macula_unprefixer, bare_id

# Add Macula prefix (n/o)
prefixed = macula_prefixer("40001001001")    # "n40001001001"

# Remove Macula prefix
unprefixed = macula_unprefixer("n40001001001")  # "40001001001"

# Remove any canon prefix
bare = bare_id("n40001001001")               # "40001001001"
```

**Boolean Conversion:**

```python
from biblealignlib.burrito import asbool

# Convert boolean to minimal string
asbool(True)   # "y"
asbool(False)  # "n"
```

## Common Workflows

### 1. Loading and Exploring Alignment Data

```python
from biblealignlib.burrito import Manager, AlignmentSet, CLEARROOT

# Configure alignment set
alset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "alignments-eng/data"
)

# Load all data
mgr = Manager(alset)

# Access specific verse
verse = mgr["40001001"]  # Matthew 1:1
verse.display()

# Explore sources and targets
print(f"Source tokens: {len(mgr.sourceitems)}")
print(f"Target tokens: {len(mgr.targetitems)}")
print(f"Verses with alignments: {len(mgr)}")
```

### 2. Searching for Specific Terms

```python
# Find all alignments containing a Greek term
jesus_alignments = mgr.token_alignments(
    "Ἰησοῦς",
    role="source",
    tokenattr="text",
    lowercase=False
)

print(f"Found {len(jesus_alignments)} alignments")

for rec in jesus_alignments[:5]:  # First 5
    print(mgr.display_record(rec))
```

### 3. Exporting Alignment Data

```python
from biblealignlib.burrito import write_alignment_group

# Get the alignment group
group = mgr.alignmentsreader.alignmentgroup

# Write to JSON
with open("output-alignments.json", "w") as f:
    write_alignment_group(group, f)

# Export filtered by books
filtered_group = mgr.alignmentsreader.filter_books(keep=("40", "41"))  # MAT, MRK
with open("output-gospels.json", "w") as f:
    write_alignment_group(filtered_group, f)
```

### 4. Working with Source Tokens

```python
from biblealignlib.burrito import SourceReader, SOURCES

# Load source data
src = SourceReader(SOURCES / "SBLGNT.tsv")

# Get token by ID
token = src["40001001001"]

# Get vocabulary
vocab = src.vocabulary(tokenattr="lemma", lower=False)
print(f"Lemma vocabulary size: {len(vocab)}")

# Find tokens by term
tokens = src.term_tokens("ἀγάπη", tokenattr="lemma", lowercase=False)
print(f"Found {len(tokens)} instances of ἀγάπη")

# Get book-level counts
book_counts = src.book_token_counts()
type_counts = src.book_type_counts(tokenattr="lemma")
```

### 5. Working with Target Tokens

```python
from biblealignlib.burrito import TargetReader, CLEARROOT

# Load target data
tr = TargetReader(
    CLEARROOT / "alignments-eng/data/targets/BSB/nt_BSB.tsv",
    detect_punc=True  # Auto-detect punctuation
)

# Get token
token = tr["40001001001"]

# Find term occurrences
love_tokens = tr.term_tokens("love", tokenattr="text", lowercase=True)

# Get source verse mappings (handles versification differences)
source_bcvs = tr.get_source_bcvs()
```

### 6. Writing Target Tokens

```python
from biblealignlib.burrito import TargetReader
from pathlib import Path

# Load tokens
tr = TargetReader(input_path)

# Define custom exclude function
def should_exclude(token):
    return token.isPunc or token.text == ""

# Write with custom fields
TargetReader.write_tsv(
    tokenlist=list(tr.values()),
    outpath=Path("output/targets.tsv"),
    excludefn=should_exclude,
    fields=("id", "text", "source_verse", "skip_space_after", "exclude")
)
```

### 7. Comparing Alignment Sets

```python
from biblealignlib.burrito import Manager, AlignmentSet, CLEARROOT

# Load two alignment sets
alset1 = AlignmentSet(sourceid="SBLGNT", targetid="BSB", targetlanguage="eng",
                      langdatapath=CLEARROOT / "alignments-eng/data")
alset2 = AlignmentSet(sourceid="SBLGNT", targetid="BSB", targetlanguage="eng",
                      langdatapath=CLEARROOT / "alignments-eng/data",
                      alternateid="auto")

mgr1 = Manager(alset1)
mgr2 = Manager(alset2)

# Compare a specific verse
verse1 = mgr1["40001001"]
verse2 = mgr2["40001001"]

diffs = verse1.diff(verse2)
if diffs:
    for diff in diffs:
        print(diff)
else:
    print("No differences found")
```

### 8. Creating Alignment Records Programmatically

```python
from biblealignlib.burrito import (
    AlignmentGroup, AlignmentRecord, AlignmentReference,
    Document, Metadata, TranslationType
)

# Create documents
source_doc = Document(docid="SBLGNT", scheme="BCVWP")
target_doc = Document(docid="BSB", scheme="BCVW")

# Create metadata
group_meta = Metadata(
    creator="My Organization",
    created=datetime.now(),
    conformsTo="0.3.1"
)

# Create alignment records
records = []
for alignment_data in my_alignment_data:
    rec_meta = Metadata(
        id=alignment_data['id'],
        origin="manual",
        status="created"
    )

    source_ref = AlignmentReference(
        document=source_doc,
        selectors=alignment_data['source_ids']
    )

    target_ref = AlignmentReference(
        document=target_doc,
        selectors=alignment_data['target_ids']
    )

    record = AlignmentRecord(
        meta=rec_meta,
        references={"source": source_ref, "target": target_ref},
        type=TranslationType()
    )
    records.append(record)

# Create group
group = AlignmentGroup(
    documents=(source_doc, target_doc),
    meta=group_meta,
    records=records
)

# Write to file
from biblealignlib.burrito import write_alignment_group
with open("new-alignments.json", "w") as f:
    write_alignment_group(group, f)
```

### 9. Validating Alignment Data

```python
# Bad records are automatically detected during Manager initialization
mgr = Manager(alset, keepbadrecords=False)  # Default: drops bad records

# Access bad records
if mgr.alignmentsreader.badrecords:
    print(f"Found {len(mgr.alignmentsreader.badrecords)} bad records")

    # Group by reason
    from collections import defaultdict
    by_reason = defaultdict(list)
    for rec_id, bad_list in mgr.alignmentsreader.badrecords.items():
        for bad in bad_list:
            by_reason[bad.reason].append(bad)

    # Display by reason
    for reason, bads in by_reason.items():
        print(f"\n{reason.value}: {len(bads)} records")
        for bad in bads[:3]:  # Show first 3
            print(f"  {bad.display}")
```

### 10. Working with Verse Data DataFrame

```python
import pandas as pd

verse = mgr["40001001"]

# Create alignment matrix
df = verse.dataframe(hitmark="✓", missmark="")

# Display in notebook
display(df)

# Export to CSV
df.to_csv("alignment-matrix.csv")

# Analyze alignment patterns
alignment_counts = (df == "✓").sum()
print(f"Alignments per target word:\n{alignment_counts}")
```

## API Reference

### Constants

```python
from biblealignlib import CLEARROOT, SOURCES

# CLEARROOT: Path to Clear-Bible repositories root
# SOURCES: Path to source TSV files
```

### Exported Classes and Functions

```python
from biblealignlib.burrito import (
    # Token classes
    BaseToken, Source, Target,

    # Readers
    SourceReader, TargetReader, AlignmentsReader,

    # Configuration
    AlignmentSet,

    # Management
    Manager, VerseData,

    # Alignment structures
    AlignmentGroup, AlignmentRecord, AlignmentReference,
    Document, Metadata,

    # Types
    TranslationType,

    # Utilities
    asbool, bare_id,
    macula_prefixer, macula_unprefixer,
    groupby_key, groupby_bcv, groupby_bcid, token_groupby_bc,
    filter_by_bcv,

    # I/O
    write_alignment_group,
)
```

### Error Handling

The module defines error types for malformed alignment records:

```python
from biblealignlib.burrito.BadRecord import Reason, BadRecord

# Reason enum values:
Reason.NOSOURCE              # No source selectors
Reason.NOTARGET              # No target selectors
Reason.EMPTYSOURCE           # Empty string in source selectors
Reason.EMPTYTARGET           # Empty string in target selectors
Reason.DUPLICATESOURCE       # Source token in multiple records
Reason.DUPLICATETARGET       # Target token in multiple records
Reason.MISSINGSOURCE         # Source token ID not found
Reason.MISSINGTARGETSOME     # Some target IDs not found
Reason.MISSINGTARGETALL      # All target IDs not found
Reason.ALIGNEDEXCLUDE        # Excluded token is aligned
Reason.UNKNOWN               # Uncategorized error
```

## Best Practices

### 1. Always Use Manager for Complete Data Access

```python
# ✓ Good: Manager coordinates all data
mgr = Manager(alset)

# ✗ Avoid: Reading individual files separately
# (unless you have a specific need)
```

### 2. Check for Bad Records

```python
mgr = Manager(alset)
if mgr.alignmentsreader.badrecords:
    print(f"Warning: {len(mgr.alignmentsreader.badrecords)} bad records found")
```

### 3. Use Appropriate ID Formats

```python
# Internal: no prefix, no part index (for most operations)
token_id = "40001001001"

# Macula format: with prefix (for export to Macula systems)
macula_id = "n40001001001"

# Always normalize when comparing
from biblealignlib.burrito import bare_id
normalized = bare_id(some_id)  # Removes prefix if present
```

### 4. Handle Versification Differences

```python
# Target tokens may reference different source verses
target = tr["44019041001"]
if not target.same_source_verse:
    print(f"Versification difference: {target.bcv} → {target.source_verse}")
```

### 5. Use VerseData for Verse-level Operations

```python
# ✓ Good: Work with complete verse data
verse = mgr["40001001"]
for src_list, trg_list in verse.alignments:
    process_alignment(src_list, trg_list)

# ✗ Avoid: Manual grouping of records
# (unless you need very specific control)
```

### 6. Validate Before Writing

```python
# Check data integrity before exporting
mgr.check_integrity()

# Verify alignment group
assert len(group.records) > 0, "No records to write"
assert group.canon in ("ot", "nt"), f"Invalid canon: {group.canon}"
```

## Additional Resources

- **Scripture Burrito Specification**: https://docs.google.com/document/d/1zR5gsrm3gIoNiHVBlWz5_BBw3N-Ew1-4M5rMsFrPzSw/
- **Clear-Bible Alignments**: https://github.com/Clear-Bible/Alignments
- **biblelib Package**: Used for BCVWPID identifier management
- **CLAUDE.md**: General repository architecture and development guidelines

## See Also

- `biblealignlib.autoalign`: Automated alignment generation
- `biblealignlib.interlinear`: Interlinear display generation
- `biblealignlib.util`: General utilities for Bible data
