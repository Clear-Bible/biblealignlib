# biblealignlib

This is a repository of code for working with Biblica's Bible text
alignments, including both automatic alignments and manually-corrected
alignments. The goal is to provide a central location that others can
both contribute to and take advantage of.

The documentation follows the best practice for project documentation
as described by Daniele Procida in the [Diátaxis documentation
framework](https://diataxis.fr/) and consists of four separate parts:

1. [Tutorials](tutorials/index.md)

## Terminology 

source
: the Hebrew or Greek source Bible text used for the alignment. The
  common sources are WLC (Westminster Leningrad Codex) for OT, and SBLGNT for NT.
  
target
: the Bible translation being aligned to a source text.

alignment 
: groups of source and target tokens that express equivalent content.
  
## Data

The public source and alignment data can be found in
https://github.com/Clear-Bible/Alignments . You are referred to the
documentation with that repository for more information on 
* data formats for source, target, and alignment data

Internal to biblica, there are language-specific repositories with
target and alignment data, along with automated alignment experimental
output, visualizations, and more. The expectation is that the best
public data will get published to the `Alignments` repository when
it's ready. 
