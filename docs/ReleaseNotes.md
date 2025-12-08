# Release Notes

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
  
  
