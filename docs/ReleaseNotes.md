# Release Notes

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
  
  
