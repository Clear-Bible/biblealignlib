"""Write data in pharaoh-format using a mapping.

# use mapper.PharaohMapper() to get a mapper instance
>>> pw = writer.PharaohWriter(mapper)
# write pharaoh data for automated alignment
>>> pw.pipedpath
PosixPath('/Users/sboisen/git/Clear-Bible/autoalignment/data/eng/BSB/SBLGNT-BSB.piped.txt')
>>> pw.write_piped()

"""

from pathlib import Path

from biblelib.word import BCVID

from biblealignlib import CLEARROOT
from .mapper import PharaohMapper


## Might want to separate out reading and writing: conflating them
## makes this code more complex
class PharaohWriter:
    """Output a set of CorpusMapping instances."""

    def __init__(
        self,
        mapper: PharaohMapper,
        pipedname: str = "",
    ) -> None:
        """Initialize the PharaohWriter for mapper."""
        self.mapper = mapper
        # encode conventions for output
        self._outdatapath: Path = CLEARROOT / "autoalignment/data"
        assert self._outdatapath.exists(), f"{self._outdatapath} must exist: need to pull the repo?"
        self.outdatapath = (
            self._outdatapath
            / self.mapper.alignmentset.targetlanguage
            / self.mapper.alignmentset.targetid
        )
        self.outdatapath.mkdir(parents=True, exist_ok=True)
        if not pipedname:
            pipedname = (
                f"{self.mapper.alignmentset.sourceid}-{self.mapper.alignmentset.targetid}.piped.txt"
            )
        self.pipedpath = self.outdatapath / pipedname

    # not clear this is still needed
    def write_pharaoh(self, outpath: Path) -> None:
        """Write pharaoh data for alignments, one line per verse (vline format).

        Example: 2-5 0-2 1-4 0-3 3-1 3-0
        """
        with outpath.open("w") as outfile:
            for bcv in self.mapper.bcv["sources"]:
                try:
                    if bcv in self.mapper.bcv["mappings"]:
                        outfile.write(
                            " ".join([f"{s}-{t}" for s, t in self.mapper.bcv_pharaoh(bcv)])
                        )
                        # writes an empty line if no alignments
                    outfile.write("\n")
                except Exception as e:
                    print(f"write_pharaoh failed on {bcv}\n{e}")

    def _write_piped(
        self,
        mappings,
        sourcetokenattr: str = "text",
        targettokenattr: str = "text",
        delimiter: str = " ||| ",
        placeholder: str = "MISSING",
    ) -> None:
        """Write out mappings.

        Abstracted so it can be called with a partial set of mapping values.
        """
        print(f"Writing data to {self.pipedpath}")
        with self.pipedpath.open("w") as outfile:
            for mapping in mappings:
                if not mapping.target_pairs and placeholder:
                    # no target text: write the placeholder value
                    targetstr = placeholder
                else:
                    targetstr = " ".join(
                        getattr(item, targettokenattr) for item, _ in mapping.target_pairs
                    )
                try:
                    sourcestr = " ".join(
                        getattr(item, sourcetokenattr) for item, _ in mapping.source_pairs
                    )
                    outfile.write(f"{sourcestr}{delimiter}{targetstr}\n")
                except Exception as e:
                    print(f"Failed on {mapping}\n{e}")

    def write_piped(
        self,
        sourcetokenattr: str = "text",
        targettokenattr: str = "text",
        delimiter: str = " ||| ",
        placeholder: str = "MISSING",
    ) -> None:
        """Write the attributes for source and target to a file.

        Format is one line per verse, 'fast_text style joint source/target pairs' with ||| separator.
        This isn't a perfect match for sentence alignment, but it's what's easy.

        self.pipedpath is used for the output directory: a different
        name can be provided when initializing PharoahMapper.

        With a non-empty string for placeholder (default is
        "MISSING"), if the target text is missing for a source, output
        the placeholder value instead. This prevents e.g. eflomal from
        breaking on partial lines.

        """
        mappings = self.mapper.bcv["mappings"].values()
        self._write_piped(mappings, sourcetokenattr, targettokenattr, delimiter, placeholder)


class PharaohPartialWriter(PharaohWriter):
    """Output a partial set of CorpusMapping instances.

    The subset is defined by start and end BCV identifiers
    (inclusive), which are incorporated into the pipedname unless it
    is supplied.

    For the Gospel of Mark:
    >>> ppw = writer.PharaohPartialWriter(pm, "41001001", "41016020")

    """

    def __init__(
        self,
        mapper: PharaohMapper,
        startbcv: str,
        endbcv: str,
        pipedname: str = "",
    ) -> None:
        """Initialize an instance"""
        assert BCVID(startbcv) < BCVID(endbcv), f"Invalid range: {startbcv} to {endbcv}"
        if not pipedname:
            pipedname = f"{mapper.alignmentset.sourceid}-{mapper.alignmentset.targetid}-{startbcv}-{endbcv}.piped.txt"
        super().__init__(mapper=mapper, pipedname=pipedname)
        self.startbcv = startbcv
        self.endbcv = endbcv
        # reset bcv mappings to the specified range

    def write_pharaoh(self, outpath) -> None:
        raise NotImplementedError()

    def write_piped(
        self,
        sourcetokenattr: str = "text",
        targettokenattr: str = "text",
        delimiter: str = " ||| ",
        placeholder: str = "MISSING",
    ) -> None:
        """Write partial piped output. Args as in superclass."""
        mappings = self.mapper.get_partial_mappings(self.startbcv, self.endbcv)
        self._write_piped(mappings, sourcetokenattr, targettokenattr, delimiter, placeholder)
