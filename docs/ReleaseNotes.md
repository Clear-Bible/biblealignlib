# Release Notes

## 0.2.2

### Bug Fixes
- **Fixed type hint** for `VerseData.aligned_targets` property (was `list[Source]`, now correctly `list[Target]`)
- **Fixed error message** in `AlignmentsReader` to reference correct attribute name
- **Type safety improvements** in `SourceReader` with explicit string conversions and `BadRecord` with tuple conversions

### Enhancements
- **Manager**: Added alignment helper methods moved from `Reader`:
  - `get_source_alignments()` returns `set[Source]` of all aligned sources
  - `get_target_alignments()` returns `dict[Target, list[list[Source]]]` supporting many-to-many alignments with warnings for duplicates
  - Fixed TypedDict for `self.bcv` to accurately represent heterogeneous structure
  - Removed unused imports (`Any`, `Union`)
- **VerseData**: Added `get_source_alignments(source)` method to retrieve targets aligned to a specific source
- **Reader**: Updated to handle nested alignment lists, creating `AlignedToken` for each source in each alignment group
- **AlignmentsReader**: Simplified type hints by removing unnecessary `Optional` wrappers

### Testing
- Added comprehensive test coverage for new alignment methods (9 tests)
- Updated all tests to handle new `dict[Target, list[list[Source]]]` return type

## 0.2.1

### Bug Fixes
- **Corrected Strong's number prefix assignment** in `biblealignlib/burrito/source.py`

### Enhancements

#### Reverse Interlinear (`interlinear` package)
- **Major Reader refactoring**:
  - Now iterates over all target tokens (not just aligned ones) for more complete coverage
  - Removed verse-level dictionary structure in favor of single `aligned_tokens` list
  - Added `exclude` parameter to optionally filter excluded target tokens
- **AlignedToken improvements**:
  - Completely rewrote comparison logic (`__lt__`) for proper sorting of aligned and
    unaligned tokens with comprehensive edge case handling
  - Added `display()` method to show token IDs in (target, source) format

#### Core Alignment Data Structures (`burrito` package)
- **AlignmentRecord**: Added `target_bcv` property to complement existing `source_bcv`,
  with refactored internal `_token_bcv()` helper method for both
- **VerseData**: Clarified docstring to explicitly note that target BCVs may not match
  source BCVs due to versification differences
- **Manager**:
  - Refactored `make_versedata()` to correctly assign target tokens based on actual
    alignment records rather than BCV matching, fixing issues with versification
    differences
  - Added `get_source_alignments()` method to return set of aligned source tokens
  - Added `get_target_alignments()` method to return target-to-source mapping
- **TargetReader**: Added `get_target_sources()` method to return mapping from target
  tokens to their corresponding source BCVs

### Testing
- **Enhanced Testing**: Added comprehensive test suite for the `interlinear` package
  in new test files.
- Updated existing tests to reflect API changes in `Manager`, `AlignmentGroup`,
  `VerseData`, and `Source` classes

## 0.2.0 - Added Coverage Package

New package for assessing alignment coverage at token, verse, and book levels.

**Components:**
- **`CoverageAnalyzer`** - Main analysis engine with caching
- **`CoverageFilter`** - Flexible filtering (ALL, CONTENT, NONEXCLUDED, CONTENT_NONEXCLUDED)
- **`CoverageExporter`** - Export utilities for reports

**Data Models:**
- `TokenCoverage` - Individual token alignment status
- `VerseCoverage` - Verse-level coverage statistics
- `BookCoverage` - Book-level aggregated coverage with contextual metrics
- `GroupCoverage` - Group/corpus-level coverage statistics

**Export Formats:**
- DataFrame (Pandas)
- TSV (tab-separated values)
- Summary reports (human-readable text)

#### Enhanced Book-Level Metrics

`BookCoverage` now provides contextual metrics distinguishing between verses with alignment data and the entire book:

| Metric | Description |
|--------|-------------|
| `source_coverage_pct` | % of tokens aligned within verses that have alignment data |
| `source_token_aligned_pct` | % of ALL tokens in the entire book that are aligned |
| `verse_coverage_pct` | % of ALL verses in the book that have alignment data |
| `verses_with_alignments` | Count of verses with alignment data vs. total verses |
| `source_token_count` | Total source tokens in entire book |
| `verse_count` | Total verses in book |


## 0.1.17

- **Unaligned Token Retrieval**: Added methods to `burrito.VerseData` for
  identifying and displaying tokens without alignments:
  - `unaligned_sources` property: Returns list of source tokens that are not
    aligned to any target tokens
  - `unaligned_targets` property: Returns list of target tokens (excluding
    those marked as excluded) that are not aligned to any source tokens
  - `unaligned()` method: Display unaligned tokens for a given type
    (sources or targets) with optional control over excluded targets
  These enhancements improve the ability to inspect alignment coverage and
  identify gaps within a verse.
- **Enhanced Testing**: Added comprehensive test suite for `burrito.VerseData`
  in new `tests/biblealignlib/burrito/test_VerseData.py` file, covering
  initialization, representation, unaligned token detection (sources and
  targets), text retrieval methods (`get_texts()`, `get_pairs()`), and edge
  cases with excluded targets (15 new tests).
- **Dependencies**: Updated `biblelib` to version 0.3.28 (from
  ^0.3.18) for improved connection checking and a bug fix.

## 0.1.16

- **Enhanced Testing**: Added comprehensive test suite for BadRecord
  detection in new `tests/biblealignlib/burrito/test_BadRecord.py` file,
  covering all 8 error types (NOSOURCE, EMPTYSOURCE, NOTARGET, EMPTYTARGET,
  MISSINGSOURCE, MISSINGTARGETSOME, MISSINGTARGETALL, ALIGNEDEXCLUDE) plus
  tests for valid records, repr/display formatting, and multi-token alignments.
  Reorganized tests to follow module structure conventions (12 new tests).


## 0.1.15

- **Python 3.13 Support**: Updated Python version constraint to support
  Python 3.10-3.13. Updated development dependencies (mypy 1.0+, pytest
  8.0+, pre-commit 4.0+, tox 4.0+) and documentation dependencies (mkdocs
  1.6+, mkdocs-material 9.0+) for compatibility.
## 0.1.14

- **New Documentation**: Added comprehensive documentation for the
  burrito module in `docs/burrito.md` covering core concepts, all key
  classes, common workflows, and API reference with extensive code
  examples.
- **New CLAUDE.md**: Added repository architecture guide for Claude
  Code with development commands, high-level code structure, core
  abstractions, data flow diagrams, and coding conventions.
- **Enhanced docstrings**: Added usage examples to
  `burrito.VerseData` and `interlinear.reverse` modules for better
  inline documentation.
- **Dependencies**: Added `jupyter-ai` and `langchain-openai` to
  support AI-enhanced Jupyter notebooks.
- Convert test fixtures to `(scope="module")` (which is how i
  _thought_ they worked): should make tests faster. 

## 0.1.13

- bug fix for `burrito.manager.make_versedata`: `Scorer` needs to be
  able to call it with an optional list of verse records.
- rehabbed `mypy` configuration in pyproject.toml
- stricter type checking and fixes for `burrito.manager`,
  `burrito.VerseData`, `util.merger`. 
  
  
## 0.1.12

- Upgrade merger to also merge when records are in both sets of
  alignments and have no differences; otherwise losing good data. 

## 0.1.11

- Trivial addition `util.merger.Merger`: type hint, comment for future work.

## 0.1.10

- Bug fix to `burrito.VerseData.VerseData.diff()`: don't add a
  suprious extra list layer to return.

## 0.1.9

- Improvements to `util.merger.Merger`.

## 0.1.8

- Add `util.merger.Merger.show_diffs` for displaying overlapping
  differences between two sets of multiple alignments.

## 0.1.7

- Add `util.merger` code for merging multiple alignments on the same
  data. Still WIP. 
- Bug fix for `VerseData.repr()`. 

## 0.1.6

- Add `note` attribute to `burrito.AlignmentGroup.Metadata`, since
  ClearAligner is now exporting notes from aligners. 

## 0.1.5

- Renamed `burrito.util.groupby_bc` to groupby_key: it's more general
  than just BC strings. Also adding sorting, which is required for
  `itertools.groupby` to work correctly.
- Added `burrito.source.content_token_dict`. 

## 0.1.4

- Some updates in `autoalign` to simplify the eflomal end-to-end
  process.
- Numerous notebook updates
  
## 0.1.3

- add ALIGNMENTSDATA variable for CLEARROOT/Alignments/data

## 0.1.2

- Add `python-dotenv` dependency, and use that with .env file or
  environment variables to set CLEARROOT and SOURCES

## 0.1.1

- Add `autoalign` module and `eflomal` in pyproject.toml file.
  
  
## 0.1.0

- Initial release as a pip-installable package. Created from the
  current code in internal-alignments/src/burrito. 
  
  
