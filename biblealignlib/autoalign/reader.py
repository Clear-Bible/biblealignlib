"""Read data in pharaoh-format and convert to Burrito format.

# use mapper.PharaohMapper() to get a mapper instance
>>> pr = reader.PharaohReader(mapper)
>>> pr.make_burrito(condition="myexpdirname")
"""

from itertools import groupby, zip_longest
from pathlib import Path

from biblealignlib.burrito import (
    AlignmentGroup,
    AlignmentRecord,
    AlignmentReference,
    Metadata,
    Source,
    Target,
    util,
    write_alignment_group,
)
from .mapper import PharaohMapper


class PharaohReader:
    """Read pharaoh data and convert to Scripture Burrito format.

    On initialization, loads existing data. read_pharaoh() then
    returns a new AlignmentGroup for the output of an automated
    algorithm.

    """

    # maybe hand in the PharaohReader instance??
    def __init__(
        self,
        mapper: PharaohMapper,
        conformsTo: str = "0.3",
        origin: str = "eflomal",
        status: str = "created",
    ):
        """Initialize the PharaohMapper."""
        self.mapper = mapper
        self.alignmentsreader = mapper.alignmentsreader
        self.alignmentset = mapper.alignmentset
        self.origin = origin
        self.status = status
        self.metadata = Metadata(conformsTo=conformsTo, origin=self.origin)

    # this should take a line of pharaoh output and return a list of AlignmentRecords
    def records_from_line(self, bcv: str, line: str) -> list[AlignmentRecord]:
        """Convert pharaoh data from a line and return a list of AlignmentRecords."""
        # like [(0, 0), (1, 1), (1, 2), (0, 3), (1, 4) ...]
        pharaoh_pairs: list[tuple[int, ...]] = [
            tuple(map(int, pair.split("-", 1))) for pair in line.split(" ")
        ]
        # these should be correct if the data respects versification: CHECK
        sourcemap = {index: item for item, index in self.mapper.bcv["mappings"][bcv].source_pairs}
        targetmap = {index: item for item, index in self.mapper.bcv["mappings"][bcv].target_pairs}
        # first need to group multiple indices for the same source or target
        # fast_align maps multiple source indices to the same target index
        # list of pairs, with each pair member a list indices
        # REPLACE with util.groupby_bcv?
        grouped: list[tuple[list[int], list[int]]] = [
            (
                [k],
                [item[1] for item in g],
            )
            for k, g in groupby(sorted(pharaoh_pairs), lambda p: p[0])
        ]
        groupedtokens: list[tuple[list[Source], list[Target]]] = [
            (
                [sourcemap.get(sindex, "MISSING") for sindex in group[0]],
                [targetmap.get(tindex, "MISSING") for tindex in group[1]],
            )
            for group in grouped
        ]
        records: list[AlignmentRecord] = []
        for index, pair in enumerate(groupedtokens):
            srcselectors = [(item.id if hasattr(item, "id") else "MISSING") for item in pair[0]]
            trgselectors = [(item.id if hasattr(item, "id") else "MISSING") for item in pair[1]]
            commonmetadata: Metadata = Metadata(
                id=f"{bcv}.{str(index+1).zfill(3)}", origin=self.origin, status=self.status
            )
            alrec = AlignmentRecord(
                meta=commonmetadata,
                references={
                    "source": AlignmentReference(
                        document=self.alignmentsreader.sourcedoc, selectors=srcselectors
                    ),
                    "target": AlignmentReference(
                        document=self.alignmentsreader.targetdoc, selectors=trgselectors
                    ),
                },
            )
            records.append(alrec)
        return [rec for rec in records if not rec.incomplete]

    def display_record(self, alrec: AlignmentRecord) -> None:
        """Print a display for an AlignmentRecord for debugging."""
        pairs = zip_longest(
            [self.sourceitems[sel] for sel in alrec.source_selectors],
            [self.targetitems[sel] for sel in alrec.target_selectors],
        )
        for src, trg in pairs:
            print(f"{alrec.source_bcv} ------------")
            print(f"Source: {src._display if src else 'None'}")
            print(f"Target: {trg._display if trg else 'None'}")
            # print(f"Source: {"; ".join(src)}")
            # print("; ".join(src), "\t", "; ".join(trg))

    def _get_partial_records(
        self,
        records,
        startbcv: str,
        endbcv: str,
    ) -> list[AlignmentRecord]:
        """Return only the records defined by start/endbcv, inclusive."""
        partial: list[AlignmentRecord] = util.filter_by_bcv(
            items=records,
            startbcv=startbcv,
            endbcv=endbcv,
            key=lambda record: record.source_bcv,
        )
        return partial

    def read_pharaoh(
        self,
        inpath: Path,
        startbcv: str = "",
        endbcv: str = "",
    ) -> AlignmentGroup:
        """Read pharaoh-format data from a file and an AlignmentGroup.

        This maps the pharaoh indices back to their source/target
        token instances (AKA Exodus: let my tokens go).

        This relies on the assumption that the pharaoh format is one
        line per verse, corresponding to the output of write_piped,
        one line per verse.

        """
        with inpath.open() as infile:
            # read using the mappings, since that's how we wrote.
            # this will still be off if you manually delete incomplete lines from the piped file!
            self.bcv_lines = list(zip(self.mapper.bcv["mappings"], infile.readlines()))
            records = [
                alrec
                for bcv, line in self.bcv_lines
                if bcv in self.mapper.bcv["mappings"]
                for alrec in self.records_from_line(bcv, line)
            ]
            # reduce records if partial
            if startbcv and endbcv:
                records = self._get_partial_records(records, startbcv, endbcv)
            return AlignmentGroup(
                documents=(self.alignmentsreader.sourcedoc, self.alignmentsreader.targetdoc),
                meta=self.metadata,
                records=records,
            )

    def make_burrito(
        self,
        condition: str,
        outname: str = "",
        startbcv: str = "",
        endbcv: str = "",
        algorithm: str = "eflomal",
    ) -> None:
        """Read pharaoh and write burrito. This is a wrapper.

        Condition is the directory name with the pharaoh data, and
        where the output is written. Assumes usual naming conventions.

        With startbcv and endbcv, only write a subset of records,
        inclusive of endbcv.

        """
        if not outname:
            if startbcv and endbcv:
                outname = f"{self.alignmentset.sourceid}-{self.alignmentset.targetid}-{algorithm}{startbcv}{endbcv}.json"
            else:
                outname = (
                    f"{self.alignmentset.sourceid}-{self.alignmentset.targetid}-{algorithm}.json"
                )
        conditiondir = (
            self.alignmentset.langdatapath.parent / "exp" / self.alignmentset.targetid / condition
        )
        assert conditiondir.exists(), f"Invalid condition directory: {conditiondir}"
        hypag = self.read_pharaoh(
            inpath=(conditiondir / "pharaoh.txt"), startbcv=startbcv, endbcv=endbcv
        )
        hypout = conditiondir / outname
        with hypout.open("w") as f:
            write_alignment_group(hypag, f)
