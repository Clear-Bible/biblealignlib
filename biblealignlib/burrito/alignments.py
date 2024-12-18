"""Read alignments data.

This provides support for manager.Manager to read the combination of source, target, and alignment data.

>>> from biblealignlib.burrito import CLEARROOT, AlignmentSet, alignments
# your local copy of alignments-eng/data
>>> LANGDATAPATH = CLEARROOT / "alignments-eng/data"
>>> alset = AlignmentSet(targetlanguage="eng", targetid="BSB", sourceid="SBLGNT", langdatapath=LANGDATAPATH)
>>> alreader = alignments.AlignmentsReader(alset)
>>> alreader.read_alignments()
# in the Manager context, when you have sources and targets, you can clean up the data
# >>> alreader.clean_alignments(mgr.sourceitems, mgr.targetitems)

# write out an alignment group 'hypag': maybe converted from pharaoh data
>>> expdir = alsetref.langdatapath.parent / "exp/BSB/eftest20241205b"
>>> hypout = (expdir / "SBLGNT-BSB-eftestlemma.json")
>>> with hypout.open("w") as f:
...   alignments.write_alignment_group(hypag, f)

"""

from collections import defaultdict
import json
from typing import Any, Optional, TextIO


from .AlignmentGroup import Document, Metadata, AlignmentGroup, AlignmentReference, AlignmentRecord
from .AlignmentSet import AlignmentSet
from .AlignmentType import TranslationType
from .BadRecord import BadRecord, Reason
from .source import SourceReader, macula_unprefixer
from .target import TargetReader


def bad_reason(
    arec: AlignmentRecord, sourceitems: SourceReader, targetitems: TargetReader
) -> Optional[BadRecord]:
    """Return a reason instance if the alignment record is malformed, or ''.

    Optionally add a tuple of supporting data.
    """
    # internally, we don't use macula prefixes (only on output)
    arecdict = arec.asdict(withmaculaprefix=False)
    badrecdict = {"identifier": arec.identifier, "record": arec}
    # these labels must match what's in BadRecord._reasons
    if not arecdict["source"]:
        return BadRecord(**badrecdict, reason=Reason.NOSOURCE)
    elif "" in arecdict["source"]:
        return BadRecord(**badrecdict, reason=Reason.EMPTYSOURCE)
    elif not (arecdict["target"]):
        return BadRecord(**badrecdict, reason=Reason.NOTARGET)
    elif "" in arecdict["target"]:
        return BadRecord(**badrecdict, reason=Reason.EMPTYTARGET)
    elif any(targetitems[sel].exclude for sel in arecdict["target"]):
        excluded = [sel for sel in arecdict["target"] if targetitems[sel].exclude]
        return BadRecord(**badrecdict, reason=Reason.ALIGNEDEXCLUDE, data=excluded)
    elif any([(sel not in sourceitems) for sel in arecdict["source"]]):
        missing = [sel for sel in arecdict["source"] if sel not in sourceitems]
        return BadRecord(**badrecdict, reason=Reason.MISSINGSOURCE, data=missing)
    elif any([(sel not in targetitems) for sel in arecdict["target"]]):
        missing = [sel for sel in arecdict["target"] if sel not in targetitems]
        if set(arecdict["target"]).symmetric_difference(set(missing)):
            return BadRecord(**badrecdict, reason=Reason.MISSINGTARGETSOME, data=missing)
        else:
            return BadRecord(**badrecdict, reason=Reason.MISSINGTARGETALL, data=missing)
    else:
        return None


class AlignmentsReader:
    """Read alignments data from a JSON file.

    This does not check for bad records, so
    self.alignmentgroup.records aren't yet filtered:
    Manager.get_alignmentsreader() calls those functions.

    """

    scheme = "BCVWP"
    altype: TranslationType = TranslationType()

    def __init__(
        self,
        alignmentset: AlignmentSet,
        keeptargetwordpart: bool = False,
        # if True, don't remove bad records
        keepbadrecords: bool = False,
        # if True, keep rejected records
        keeprejected: bool = False,
    ) -> None:
        """Initialize a Reader instance."""
        self.alignmentset: AlignmentSet = alignmentset
        self.keeptargetwordpart: bool = keeptargetwordpart
        self.keepbadrecords: bool = keepbadrecords
        # the configuration of alignment data
        self.alignmentset: AlignmentSet = alignmentset
        # Document instances for AlignmentGroup
        self.sourcedoc: Document = Document(docid=self.alignmentset.sourceid, scheme=self.scheme)
        self.targetdoc: Document = Document(docid=self.alignmentset.targetid, scheme=self.scheme)
        # Read the data and instantiate an AlignmentGroup (with
        # AlignmentRecords, etc. all the way down)
        # dict of records where status = rejected
        self.badrecords: Optional[dict[str, list[BadRecord]]] = defaultdict(list)
        self.rejected: dict[str, AlignmentRecord] = {}
        self.alignmentgroup: AlignmentGroup = self.read_alignments(keeprejected=keeprejected)
        # can't do all the checking without sources, targets, etc. Use
        # manager.Manager to read the data and collect any bad records
        # if you're not sure about it.
        #

    def _targetid(self, targetid: str) -> str:
        """Return a normalized target ID.

        With self.keeptargetwordpart = False, drop the last digit.
        """
        if not self.keeptargetwordpart and len(targetid) == 12:
            return targetid[:11]
        else:
            return targetid

    def _make_record(self, alrec: dict[str, Any]) -> Optional[AlignmentRecord]:
        """Process a single alignment record.

        Many assumptions are encoded here that probably work for
        GrapeCity data, but not necessarily others.

        """
        metadatadict = alrec["meta"]
        # upgrade patch: 0.2.1 spec renames 'process' as 'origin'
        if "process" in metadatadict:
            metadatadict["origin"] = metadatadict["process"]
            del metadatadict["process"]
        # add a missing status value; retain an existing one
        metadatadict["status"] = metadatadict["status"] if "status" in metadatadict else "created"
        meta: Metadata = Metadata(**metadatadict)
        # if no source selectors, can't compute BCV keys later, which
        # messes up later processes. So drop any record with no source
        # selectors here
        if not alrec["source"]:
            print(
                f"No source selectors for {alrec['meta']['id']}: dropping the record, adding to self.badrecords."
            )
        else:
            # convert Macula IDs to token IDs (no prefix)
            alrec["source"] = [macula_unprefixer(src) for src in alrec["source"]]
        sourceref: AlignmentReference = AlignmentReference(
            document=self.sourcedoc, selectors=alrec["source"]
        )
        # bad hack here to drop word parts
        trgselectors = [self._targetid(trgid) for trgid in alrec["target"]]
        targetref: AlignmentReference = AlignmentReference(
            document=self.targetdoc, selectors=trgselectors
        )
        return AlignmentRecord(
            meta=meta, references={"source": sourceref, "target": targetref}, type=self.altype
        )

    def read_alignments(self, keeprejected: bool = False) -> AlignmentGroup:
        """Read JSON alignments data and return an AlignmentGroup.

        Drop records whose status is rejected unless keeprejected is True (default is False).
        """
        with self.alignmentset.alignmentpath.open("rb") as f:
            agroupdict = json.load(f)
            if isinstance(agroupdict, list):
                raise ValueError(
                    f"{self.alignmentspath} should contain an object, not a list. Perhaps not converted to Burrito"
                    " format yet?"
                )
            meta: Metadata = Metadata(**agroupdict["meta"])
            # assumes default TranslationType to match self.altype,
            # and one value for the whole group: true for GC data, not
            # necessarily others
            assert (
                agroupdict["type"] == self.altype.type
            ), f"Unexpected alignment type: {agroupdict['type']}"
            records: list[AlignmentRecord] = [
                record
                for alrec in agroupdict["records"]
                if (record := self._make_record(alrec))
                if record
            ]
            # capture rejected records
            self.rejected = {
                recid: rec
                for rec in records
                if rec.meta.status == "rejected"
                if (recid := rec.meta.id)
            }
            # drop rejected records
            if not keeprejected:
                records = [rec for rec in records if rec.meta.id not in self.rejected]
                if self.rejected:
                    print(f"Dropping {len(self.rejected)} rejected records")
            return AlignmentGroup(
                documents=(
                    self.sourcedoc,
                    self.targetdoc,
                ),
                meta=meta,
                records=sorted(records),
                # should be the same throughout
                roles=records[0].roles,
            )

    def _clean_corpus(
        self,
        records: dict[str, list[AlignmentRecord]],
    ) -> None:
        """Check records across the corpus and add to self.badrecords.

        Works by side-effect so it can append to existing bad records
        for a record id if necessary.

        """

        def _flag_dupes(dupedict: dict[str, list[AlignmentRecord]], reason: Reason) -> None:
            for firstbad, records in dupedict.items():
                for rec in records:
                    # all records with duplicates are marked as bad
                    recid = rec.identifier
                    badrec = BadRecord(
                        identifier=recid,
                        record=rec,
                        reason=reason,
                        data=firstbad,
                    )
                    self.badrecords[recid].append(badrec)

        sourceselectors: dict[str, list[AlignmentRecord]] = defaultdict(list)
        targetselectors: dict[str, list[AlignmentRecord]] = defaultdict(list)
        for rec in records.values():
            for srcsel in rec.source_selectors:
                sourceselectors[srcsel].append(rec)
            for trgsel in rec.target_selectors:
                targetselectors[trgsel].append(rec)
        # check for selectors that are included in multiple records
        sourcedupes = {
            ssel: records for ssel, records in sourceselectors.items() if len(records) > 1
        }
        targetdupes = {
            tsel: records for tsel, records in targetselectors.items() if len(records) > 1
        }
        _flag_dupes(sourcedupes, Reason.DUPLICATESOURCE)
        _flag_dupes(targetdupes, Reason.DUPLICATETARGET)
        return None

    def clean_alignments(self, sourceitems: SourceReader, targetitems: TargetReader) -> None:
        """Drop bad records, and populate self.badrecords."""
        alrecdict: dict[str, AlignmentRecord] = {
            arec.meta.id: arec for arec in self.alignmentgroup.records
        }
        for recid, arec in alrecdict.items():
            if badrec := bad_reason(arec, sourceitems, targetitems):
                self.badrecords[recid].append(badrec)
        # also check across the corpus
        self._clean_corpus(alrecdict)
        if self.badrecords:
            keepmsg = "Keeping" if self.keepbadrecords else "Dropping"
            print(
                f"{keepmsg} {len(self.badrecords)} bad alignment records. Instances in self.alignmentsreader.badrecords."
            )
            for reason in Reason:
                rcount = len(
                    [
                        mal
                        for mallist in self.badrecords.values()
                        for mal in mallist
                        if mal.reason == reason
                    ]
                )
                if rcount:
                    print(f"{reason.value}\t{rcount}")
        # drop them from group records, unless keeping them
        if not self.keepbadrecords:
            self.alignmentgroup.records = [
                rec for recid, rec in alrecdict.items() if recid not in self.badrecords
            ]
        return None

    def filter_books(self, keep: tuple = ()) -> AlignmentGroup:
        """Drop any records from group whose books aren't in keep.

        keep is a list of book IDs, like ("40", "41", "56") (that is,
        MAT, MRK, TIT).

        """
        filtered = [
            rec
            for rec in self.alignmentgroup.records
            if ((bcv := rec.source_bcv) and (bcv[:2] in keep))
        ]
        return AlignmentGroup(
            documents=self.alignmentgroup.documents, meta=self.alignmentgroup.meta, records=filtered
        )


# copied from gc2sb.manager.write_alignment_group with minor changes
def write_alignment_group(group: AlignmentGroup, f: TextIO, hoist: bool = True) -> None:
    """Write JSON data for an arbitrary group in Scripture Burrito format.

    Writes some of the JSON by hand to get records on the same line.
    """

    def _write_documents(out: TextIO, documents: tuple[Document, Document]) -> None:
        """Write documents tuple to out."""
        out.write(' "documents": [\n')
        out.write("    " + json.dumps(documents[0].asdict()) + ",\n")
        out.write("    " + json.dumps(documents[1].asdict()) + "\n")
        out.write(" ],\n")

    def _write_meta(out: TextIO, meta: Metadata) -> None:
        """Write metdatadata to out."""
        metarow = '"meta": ' + json.dumps(meta.asdict())
        f.write(f" {metarow},\n")

    f.write("{\n")
    _write_documents(f, group.documents)
    _write_meta(f, group.meta)
    f.write(f' "roles": {json.dumps(group.roles)},\n')
    f.write(f' "type": "{group._type}",\n "records": [\n ')
    for arec in group.records[:-1]:
        json.dump(arec.asdict(), f)
        f.write(",\n ")
    # now the last one without a comma, because JSON
    json.dump(group.records[-1].asdict(), f)
    f.write("\n ]}")
