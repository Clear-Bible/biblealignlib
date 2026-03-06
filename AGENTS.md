# biblealignlib Architecture Guide

biblealignlib is a Python library for managing word-level alignments
between Bible source texts (Hebrew/Greek manuscripts) and target
translations. It implements the Scripture Burrito Alignment Standard
v0.3 and supports both manual alignment curation and automated
alignment verification.

## Key Principles

- Write concise, technical responses with accurate Python examples.
- Prioritize clarity, data integrity, and best practices in Biblical data processing workflows.
- Use dataclasses for structured data modeling and functional programming for data processing pipelines.
- Implement proper data validation and error handling when working with Biblical references and entity data.
- Use descriptive variable names that reflect Biblical concepts and entities they represent.
- Follow PEP 8 style guidelines for Python code.
- Keep consistent with existing conventions in the code.

Error Handling and Data Validation:
- Use try-except blocks for error-prone operations, especially in data parsing and Biblical reference conversion.
- Implement proper validation for Biblical references using biblelib.
- Use appropriate error handling for missing or malformed entity data.

Performance and Data Management:
- Utilize efficient data structures for large Biblical datasets.
- Implement proper caching strategies for frequently accessed entity data.
- Use appropriate serialization methods (JSON, YAML) for data persistence.
- Profile data processing pipelines to identify and optimize bottlenecks.

## Project Organization

The library is organized around two main domains:

### Core Modules

**biblealignlib/burrito/** - Core data structures and I/O for Scripture Burrito format

- **BaseToken.py**: Base dataclass for all tokens (source/target), handles BCVWPID identifiers
- **source.py**: Source token model (manuscripts), carries linguistic metadata (lemma, morphology, Strong's numbers)
- **target.py**: Target token model (translations), includes alignment metadata (excluded, required, primary flags)
- **AlignmentGroup.py**: High-level alignment data structures (Document, Metadata, AlignmentRecord, AlignmentGroup)
- **AlignmentSet.py**: Configuration for a specific alignment dataset (paths, IDs for source/target)
- **AlignmentType.py**: Enum-like classes for alignment types (TranslationType, DirectedType, AnaphoraType, etc.)
- **manager.py**: Central Manager class - UserDict that loads and organizes all data for an alignment set
- **VerseData.py**: Per-verse view of alignments with convenience methods (dataframe, get_pairs, etc.)
- **alignments.py**: JSON I/O for Scripture Burrito alignment data
- **util.py**: Grouping and filtering utilities for token collections
- **BadRecord.py**: Tracks malformed alignment records

**biblealignlib/autoalign/** - Support for automated alignment algorithms

- **mapper.py**: PharaohMapper - converts internal Burrito format to pharaoh-style index pairs
- **reader.py**: PharaohReader - converts pharaoh format back to Scripture Burrito JSON
- **writer.py**: PharaohWriter - outputs data in pharaoh "piped" format for external tools
- **scorer.py**: Scoring system against gold standard alignment data
- **Score.py**: Dataclasses for alignment quality metrics (precision, recall, F1, AER)
- **corpusmapping.py**: CorpusMapping - intermediate structure for verse-level mappings
- **eflomal.py**: (External tool integration - optional)
- **runeflomal.py**: (External tool integration - optional)

**biblealignlib/interlinear/** - Support for interlinear/reverse-interlinear generation

- **token.py**: AlignedToken - wraps a source+target pair for display
- **reverse.py**: Reverse interlinear generation

**biblealignlib/util/** - General utilities

- **vocab.py**: Vocabulary/frequency analysis
- **merger.py**: Merging alignment data

**biblealignlib/** - Package initialization and configuration

- **__init__.py**: Environment setup (CLEARROOT, SOURCES paths), SourceidEnum, canon utility functions
- **strongs.py**: Strong's number normalization

## Core Data Model

### Token Identifiers (BCVWPID)

Tokens use identifiers in BCVWPID format:

- **B** (Book): 2 digits (01-66 standard Protestant canon)
- **C** (Chapter): 3 digits
- **V** (Verse): 3 digits  
- **W** (Word): 3 digits (position in verse)
- **P** (Part): 1 digit (subword unit, mainly for source texts)

Example: `n41004003001` = Mark 4:3, word 1 (with 'n' NT prefix for manuscripts)

The first character can be an optional canon prefix: 'o' for OT, 'n' for NT.

### Key Abstractions

**BaseToken** (base class for Source and Target)

- `id`: BCVWPID identifier
- `text`: Surface form or omitted for copyrighted texts
- `altId`: Alternate identifier variant
- `aligned`: Display flag for UI
- Properties: `bcv`, `bare_id`, `isempty`

**Source** (manuscript token, extends BaseToken)

- `strong`: Strong's number (G/H prefixed)
- `lemma`: Lemmatized form
- `morph`: Morphological analysis
- `gloss`, `gloss2`: English explanations
- `pos`: Part of speech
- Computed: `is_content` (noun/verb/adj/adv for filtering)

**Target** (translation token, extends BaseToken)

- `source_verse`: BCV of corresponding source verse (handles versification differences)
- `exclude`: Boolean - token ineligible for alignment
- `required`: Boolean - token must be aligned
- `skip_space_after`: Boolean - concatenate with next token in display
- `isPunc`: Boolean - is this punctuation
- `isPrimary`: Boolean - primary alignment for multi-aligned tokens
- `transType`: Translation type (empty string to preserve)

### Alignment Data Structures

**AlignmentRecord** - Single word/phrase alignment

- `meta`: Metadata (status, origin, creator, note, created timestamp)
- `references`: Dict mapping role name → AlignmentReference
  - Source reference: list of source token IDs
  - Target reference: list of target token IDs
- `type`: AlignmentType (TranslationType by default)

**AlignmentReference** - Wrapper for token selector lists

- `document`: Document (docid, scheme)
- `selectors`: List of token IDs
- `incomplete`: Property checking for MISSING markers

**AlignmentGroup** - Collection of all alignment records for a document pair

- `documents`: Tuple of (source_doc, target_doc)
- `meta`: Group-level metadata
- `records`: List of AlignmentRecord instances
- Methods: `verserecords()` returns dict of BCV → list of records

**VerseData** - Verse-level view (created by Manager)

- `bcvid`: Verse identifier
- `alignments`: List of (source_list, target_list) tuples
- `sources`: List of Source tokens in verse
- `targets`: List of Target tokens
- `targets_included`: Computed tuple of non-excluded targets
- `records`: Tuple of AlignmentRecord instances
- Methods for display/analysis:
  - `get_pairs()`: Returns (source, target) tuples
  - `dataframe()`: Pandas DataFrame with hit matrix
  - `get_texts()`: Extract text attributes with optional uniqueness
  - `diff()`: Compare two VerseData instances

### Data Flow

**Reading Alignment Data:**
```
AlignmentSet (configuration)
  ↓
Manager.__init__()
  ├─ SourceReader (loads TSV → dict of Source tokens)
  ├─ TargetReader (loads TSV → dict of Target tokens)
  ├─ AlignmentsReader (loads JSON → AlignmentGroup)
  └─ Manager[bcvid] → VerseData instances
      └─ Combines sources, targets, records by verse
```

**Writing Alignment Data:**
```
Source/Target tokens
  ↓
Manual/Automated alignments → AlignmentGroup
  ↓
write_alignment_group() → JSON file (Scripture Burrito format)
```

**Automated Alignment Workflow:**
```
Manager (reference/gold-standard data)
  ↓
PharaohMapper (converts to index pairs)
  ↓
PharaohWriter → pharaoh "piped" format
  ↓
[External tool: eflomal, fast_align, etc.]
  ↓
PharaohReader (pharaoh format → Scripture Burrito)
  ↓
Scorer (compares against reference, metrics)
```

## Configuration & Paths

### Environment Setup

biblealignlib expects a `.env` file defining:
```
CLEARROOT=/path/to/Clear-Bible
```

Defaults to `~/git/Clear-Bible` if not set.

Key paths computed from CLEARROOT:
- `ALIGNMENTSDATA`: `{CLEARROOT}/Alignments/data` - Published alignment data
- `SOURCES`: `{CLEARROOT}/Alignments/data/sources` - Source TSVs (SBLGNT.tsv, WLC.tsv, etc.)

Language-specific data paths:
- `{CLEARROOT}/alignments-{lang}/data/sources/` - Target TSVs
- `{CLEARROOT}/alignments-{lang}/data/alignments/{target}/` - JSON alignment files
- `{CLEARROOT}/autoalignment/data/{lang}/{target}/` - Pharaoh-format output

### AlignmentSet Configuration

AlignmentSet encapsulates paths for a dataset:
```python
AlignmentSet(
    sourceid="SBLGNT",      # One of SourceidEnum
    targetid="BSB",          # Target version ID
    targetlanguage="eng",    # ISO 639-3 code
    langdatapath=Path(...),  # Path to alignments-{lang}/data
    alternateid="manual"     # Subdirectory/suffix (manual, auto, etc.)
)
```

File naming convention:
- Source: `{sourceid}.tsv`
- Target: `{langdatapath}/targets/{targetid}/{canon}_{targetid}.tsv`
- Alignment: `{langdatapath}/alignments/{targetid}/{sourceid}-{targetid}-{alternateid}.json`

## Important Patterns

### Identifier Handling
- Always use BCVWPID format internally
- Macula prefixes ('o', 'n') are added on serialization, stripped on load
- `macula_prefixer()` / `macula_unprefixer()` handle this conversion
- Many APIs accept either bare IDs or prefixed IDs

### Token Grouping
Utilities in `burrito.util` for organizing tokens:
- `groupby_key()`: Generic grouping by key function
- `groupby_bcv()`: Group by full verse (default for most uses)
- `token_groupby_bc()`: Group by book+chapter
- `groupby_bcid()`: Group IDs by book+chapter
- `filter_by_bcv()`: Slice tokens by verse range

### Boolean Handling
Target tokens have boolean fields stored as strings in TSV:
- `asbool()`: Convert True/False → "y"/"n"
- `_truthy_asbool()`: Convert "y"/"true" (case-insensitive) → True

### Alignment Metadata
Every alignment record tracks:
- `origin`: How it was created (manual, eflomal, fast_align, etc.)
- `status`: Workflow state (created, in_progress, reviewed, finalized, etc.)
- `creator`: Who/what tool created it
- `note`: Free-form annotation
- `created`: Timestamp

### Scoring Metrics
Used for automated alignment evaluation:
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1**: Harmonic mean of precision and recall
- **AER** (Alignment Error Rate): 1 - Precision (alternative metric)

## Test Structure

Tests use pytest with module-scoped fixtures:

```
tests/biblealignlib/
├── burrito/
│   ├── test_BaseToken.py
│   ├── test_source.py
│   ├── test_target.py
│   ├── test_manager.py
│   ├── test_alignments.py
│   ├── test_AlignmentGroup.py
│   ├── test_AlignmentSet.py
│   ├── test_AlignmentType.py
│   └── test_BadRecord.py
├── autoalign/
│   └── test_Score.py
├── test_init.py
└── test_strongs.py
```

**Fixture Pattern:**
- Module-scoped fixtures for expensive setup (loading alignment data)
- Fixtures parameterized by AlignmentSet config
- Reference data from published SBLGNT-BSB or other stable pairs
- Tests verify internal consistency, not absolute data values

Example fixture usage:
```python
@pytest.fixture(scope="module")
def sblgntbsb() -> AlignmentSet:
    """Return a AlignmentSet instance."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=CLEARROOT / "Alignments/data/eng"
    )

@pytest.fixture(scope="module")
def mgr(sblgntbsb: AlignmentSet) -> Manager:
    """Return a Manager instance."""
    return Manager(sblgntbsb)

class TestManager:
    def test_init(self, mgr: Manager) -> None:
        assert mgr.alignmentset.sourceid == "SBLGNT"
```

## Conventions & Best Practices

### Type Hints
- Full type hints required (mypy with `disallow_untyped_defs`)
- Use Optional[] for nullable values, not Union with None
- Dataclasses use `field(default_factory=...)` for mutable defaults

### Code Style
- Black formatting (line length 100)
- isort for imports
- Docstrings on all public functions (triple-quoted)
- Use dataclasses for data models, avoid manual __init__

### Error Handling
- Assertions for internal invariants (not user input)
- Explicit ValueError/TypeError for user errors
- Warnings for recoverable issues (versification mismatches, etc.)

### Performance Considerations
- Manager loads entire alignment set at initialization (not lazy)
- VerseData computed fields in __post_init__
- Grouping operations use itertools.groupby (sorted data required)
- Token dictionaries use ID strings as keys for O(1) lookup

### Data Integrity
- AlignmentRecord validates all roles present in references
- AlignmentGroup validates single type across all records
- badrecords filtered during Manager.clean_alignments()
- Incomplete references (MISSING markers) tracked but preserved

## Dependencies

Core dependencies (from pyproject.toml):
- **biblelib**: BCVWPID handling, Bible reference utilities
- **pandas**: Data analysis, DataFrames
- **unicodecsv**: Unicode-safe TSV I/O
- **python-dotenv**: .env file loading
- **regex**: Extended regex with Unicode properties
- **altair**: Visualization (optional, for notebooks)
- **jupyter-ai**: Notebook integration (optional)

Optional/External:
- **eflomal**: Word alignment algorithm (requires special build on macOS)
- Poetry for dependency management

## Common Operations

### Load an Alignment Set
```python
from biblealignlib.burrito import Manager, AlignmentSet

alset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "alignments-eng/data"
)
mgr = Manager(alset)

# Access by verse
vd = mgr["41004003"]  # Mark 4:3
print(vd.alignments)
```

### Work with Tokens
```python
# Source tokens
src_token = mgr.sourceitems["41004003001"]
print(src_token.text, src_token.lemma, src_token.pos)

# Target tokens
tgt_token = mgr.targetitems["41004003001"]
print(tgt_token.text, tgt_token.exclude)

# Get verse texts
vd.get_texts(typeattr="targets", unique=True)
vd.get_texts(typeattr="sources")
```

### Export Alignment Data
```python
from biblealignlib.burrito import write_alignment_group

# Write AlignmentGroup to JSON
with open("output.json", "w") as f:
    write_alignment_group(alignment_group, f)
```

### Score Against Reference
```python
from biblealignlib.autoalign import scorer

# Set up scoring condition
sc = scorer.ScoreCondition(
    targetlang="eng", 
    targetid="BSB",
    condition="20241220_text"
)

# Score specific verse
verse_score = sc.score_verse("41004003")
print(verse_score.summary())

# Score all verses
all_score = sc.score_all()
print(all_score.summary_dict())
```

### Convert Pharaoh Format
```python
from biblealignlib.autoalign import reader, writer

# Write for external tool
pw = writer.PharaohWriter(targetlang="eng", targetid="BSB", sourceid="SBLGNT")
pw.write_piped()  # → piped format file

# Read back results
pr = reader.PharaohReader(
    targetlang="eng",
    targetid="BSB",
    sourceid="SBLGNT",
    condition="20241220_eflomal_text"
)
alignment_group = pr.make_burrito()
```

## Development Notes

### Testing with pytest
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/biblealignlib/burrito/test_manager.py

# Run with verbose output
pytest -v tests/

# Run with coverage
pytest --cov=biblealignlib tests/
```

### Type Checking
```bash
mypy
```

### Code Formatting
```bash
black .
isort .
```

### Known Limitations
1. No lazy loading - entire dataset must fit in memory
2. Versification differences handled post-hoc (target tokens track source_verse)
3. Sub-word alignments (morph-level) not fully supported
4. Some external tool integrations (eflomal) require special setup
5. copyrighted source texts omit surface text (empty text field)

## References

- Scripture Burrito v0.3 specification: https://docs.google.com/document/d/1zR5gsrm3gIoNiHVBlWz5_BBw3N-Ew1-4M5rMsFrPzSw/
- Clear Bible project: https://github.com/Clear-Bible
- biblelib documentation: BCVWPID reference system
- Dublin Core Metadata: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/
