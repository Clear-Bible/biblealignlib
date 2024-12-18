"""Create mappings from corpus instances (Source or Target) to pharaoh-format information.

This supports mapping to and from pharaoh-format data, which is
commonly used by automated alignment algorithms.

>>> from biblealignlib.burrito import CLEARROOT, pharaoh, AlignmentSet
>>> from biblealignlib.autoalign import pharaoh
# your local copy of alignments-eng/data
>>> targetlang, targetid, sourceid = ("eng", "BSB", "SBLGNT")
>>> alsetref = AlignmentSet(targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
>>> pm = pharaoh.PharaohMapper(alsetref)
>>> len(pm)
# this many verses have mappings
7930
>>>  pm.bcv["mappings"]["41004003"]
<CorpusMapping: 41004003>
>>> pm.bcv["mappings"]["41004003"].source_pairs
[(<Source: n41004003001>, 0), (<Source: n41004003002>, 1), (<Source: n41004003003>, 2), ...
>>> pm.bcv["mappings"]["41004003"].target_pairs
[(<Target: 410040030011>, 0), (<Target: 410040030021>, 1), (<Target: 410040030031>, 2), ...


"""

from biblealignlib.burrito import (
    AlignmentRecord,
    AlignmentSet,
    Manager,
    Source,
    Target,
    util,
)
from .corpusmapping import CorpusMapping


## Might want to separate out reading and writing: conflating them
## makes this code more complex
class PharaohMapper(Manager):
    """Map the verses of a corpus to CorpusMapping instances for output."""

    def __init__(
        self,
        alignmentset: AlignmentSet,
        # questionable, and maybe not used
        origin="manual",
        pipedname: str = "",
    ):
        """Initialize the PharaohMapper."""
        super().__init__(alignmentset=alignmentset, creator=origin)
        # get the mappings from source_verse to target tokens
        self.source_bcvs: dict[str, list[Target]] = self.targetitems.get_source_bcvs()
        # iterate over verserecords instead of versesources, which has
        # sources with no alignments (for WLCM-BSB, 19005002-19007002,
        # etc.)
        self.bcv["mappings"] = {bcv: self._get_corpusmapping(bcv) for bcv in self.bcv["records"]}

    def _source_bcv_targets(self, bcv: str) -> list[Target]:
        """Return the target tokens corresponding to alignment records for BCV.

        This is necessary because versification differences means the
        target tokens may have a different BCV from the source: the
        alignment records have the truth. The records have selectors,
        but not Token instances: those need to be retrieved.

        But NOTE:
        - these are not all the target tokens
        - the tokens are not ordered as in the target corpus.

        """
        return [
            self.targetitems[sel]
            for rec in self.bcv["records"][bcv]
            for sel in rec.target_selectors
        ]

    def _get_corpusmapping(self, bcv: str) -> CorpusMapping:
        """Return a CorpusMapping for a BCV.

        This has to follow source_verse and alignment data in case the
        target versification doesn't match the source.

        """
        sources: list[Source] = self.bcv["sources"][bcv]
        source_pairs = list(zip(sources, range(len(sources))))
        # WRONG if source_verse is different, these won't match the alignments.
        # Instead, capture from the alignments data itself, which is
        # organized by source references
        # STILL WRONG: this only returns aligned target tokens.
        # targets = self._source_bcv_targets(bcv)
        targets = self.source_bcvs[bcv]
        target_pairs = list(zip(targets, range(len(targets))))
        return CorpusMapping(bcv, source_pairs, target_pairs)

    def selector_indices(
        self, record: AlignmentRecord, mapping: CorpusMapping, typeattr: str
    ) -> list[int]:
        """Return the pharaoh indices for the record and mapping, as given by typeattr."""
        assert (
            typeattr in CorpusMapping._typeattrs
        ), f"typeattr should be one of {CorpusMapping._typeattrs}"
        itemstype = "sourceitems" if typeattr == "sources" else "targetitems"
        seltype = "source_selectors" if typeattr == "sources" else "target_selectors"
        tokenmaptype = "sourcetokenmap" if typeattr == "sources" else "targettokenmap"
        tokens = [getattr(self, itemstype)[sel] for sel in getattr(record, seltype)]
        indices = [getattr(mapping, tokenmaptype)[item] for item in tokens]
        return indices

    def record_pairs(
        self, record: AlignmentRecord, mapping: CorpusMapping
    ) -> tuple[tuple[int, int]]:
        """Return a tuple of paired indices for the tokens in the record.

        Example: Given source indices [0,1] and target indices [2],
        return ((0, 2), (1, 2)).

        """
        return [
            (src, trg)
            for src in self.selector_indices(record, mapping, "sources")
            for trg in self.selector_indices(record, mapping, "targets")
        ]

    def bcv_pharaoh(self, bcv: str) -> tuple[tuple[int, int]]:
        """Return pairs of pharaoh indices for a single verse.

        Returns an empty tuple if this BCV has no alignments.
        """
        if bcv in self.bcv["mappings"]:
            mapping = self.bcv["mappings"][bcv]
            vrecords = self.bcv["records"][bcv]
            return [pair for rec in vrecords for pair in self.record_pairs(rec, mapping)]
        else:
            return ()

    def get_partial_mappings(
        self,
        startbcv: str,
        endbcv: str,
    ) -> list[CorpusMapping]:
        """Return only the mappings defined by start and end BCV identifiers (inclusive)."""
        partial: tuple[str, CorpusMapping] = util.filter_by_bcv(
            items=self.bcv["mappings"].items(),
            startbcv=startbcv,
            endbcv=endbcv,
            key=lambda pair: pair[0],
        )
        return [par[0] for par in partial]
