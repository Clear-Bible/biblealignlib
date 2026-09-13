"""Test AlignmentsReader."""

import json
from io import StringIO

import pytest

from biblealignlib.burrito import (
    CLEARROOT,
    AlignmentSet,
    AlignmentsReader,
    AlignmentRecord,
    write_alignment_group,
)

# test internal version
ENGLANGDATAPATH = CLEARROOT / "alignments-eng/data"


@pytest.fixture(scope="module")
def sblgntbsb() -> AlignmentSet:
    """Return a AlignmentSet instance."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=ENGLANGDATAPATH,
        alternateid="manual",
    )


@pytest.fixture(scope="module")
def alreader(sblgntbsb: AlignmentSet) -> AlignmentsReader:
    """Return a AlignmentsReader instance."""
    return AlignmentsReader(sblgntbsb)


@pytest.fixture(scope="module")
def publishedset() -> AlignmentSet:
    """Return an AlignmentSet for a published, openly-licensed pair."""
    return AlignmentSet(
        sourceid="SBLGNT",
        targetid="BSB",
        targetlanguage="eng",
        langdatapath=CLEARROOT / "Alignments/data/eng",
        alternateid="manual",
    )


class TestIdentifierRoundTrip:
    """Test preserve_identifiers, and that the default is unaffected by it."""

    def test_the_default_normalizes_to_the_hub_format(self, publishedset: AlignmentSet) -> None:
        """Test that without the option, source selectors lose their canon prefix.

        This is existing behaviour and existing callers depend on it, so
        it stays the default.
        """
        reader = AlignmentsReader(publishedset, keeprejected=True)
        selectors = reader.alignmentgroup.records[0].source_selectors
        assert selectors
        assert all(not sel[:1].isalpha() for sel in selectors)

    def test_selectors_survive_a_round_trip(self, publishedset: AlignmentSet) -> None:
        """Test that with preserve_identifiers, every selector written equals the one read.

        Identifiers belong to the data creator and are opaque to us. An
        alignment whose selectors have been reshaped no longer resolves
        against the text it describes, so the environment that produced
        that text cannot use the alignment at all.
        """
        original = json.loads(publishedset.alignmentpath.read_text(encoding="utf-8"))
        reader = AlignmentsReader(publishedset, keeprejected=True, preserve_identifiers=True)
        buf = StringIO()
        write_alignment_group(reader.alignmentgroup, buf)
        written = json.loads(buf.getvalue())

        def units(records: list[dict], role: str) -> list[tuple[str, ...]]:
            """Return every reference unit for role, in a comparable order."""
            return sorted(tuple(rec[role]) for rec in records)

        for role in ("source", "target"):
            before, after = units(original["records"], role), units(written["records"], role)
            # a comparison of two empty sets would pass while checking nothing
            assert before, f"no {role} units read from {publishedset.alignmentpath}"
            assert len(before) == len(after), f"{role}: {len(before)} units in, {len(after)} out"
            differing = [(b, a) for b, a in zip(before, after) if b != a]
            assert not differing, f"{role}: {len(differing)} units altered, e.g. {differing[:3]}"


class TestAlignmentsReader:
    """Test AlignmentsReader()."""

    def test_init(self, alreader: AlignmentsReader) -> None:
        """Test initialization."""
        assert alreader.scheme == "BCVWP"
        assert alreader.sourcedoc.docid == "SBLGNT"
        assert alreader.targetdoc.docid == "BSB"
        assert not alreader.rejected
        algroup = alreader.alignmentgroup
        alrec: dict[str, AlignmentRecord] = {arec.meta.id: arec for arec in algroup.records}
        # the default normalizes selectors to the hub format
        assert alrec["41004003.001"].asdict()["source"] == ["41004003001", "41004003002"]
        assert alrec["41004003.001"].meta.id == "41004003.001"
        assert alrec["41004003.001"].identifier == "41004003.001"
