"""Test code in src.burrito.AlignmentSet."""

import pytest

from biblealignlib import CLEARROOT, SOURCES
from biblealignlib.burrito import AlignmentSet

ENGLANGDATAPATH = CLEARROOT / "alignments-eng/data"
HINLANGDATAPATH = CLEARROOT / "alignments-hin/data"


@pytest.fixture(scope="module")
def aset() -> AlignmentSet:
    """Return a AlignmentSet instance."""
    return AlignmentSet(
        sourceid="SBLGNT", targetid="LEB", targetlanguage="eng", langdatapath=ENGLANGDATAPATH
    )


@pytest.fixture(scope="module")
def asethin() -> AlignmentSet:
    """Return a AlignmentSet instance for IRVHin."""
    return AlignmentSet(
        sourceid="SBLGNT", targetid="IRVHin", targetlanguage="hin", langdatapath=HINLANGDATAPATH
    )


# # not needed for Alignments
# @pytest.fixture
# def asetinternal() -> AlignmentSet:
#     """Return a AlignmentSet instance for the legacy structure of internal-alignments."""
#     return AlignmentSet(
#         sourceid="SBLGNT", targetid="LEB", targetlanguage="eng", langdatapath=DATAPATH
#     )


class TestAlignmentSet:
    """Test the AlignmentSet class."""

    def test_init(self, aset: AlignmentSet) -> None:
        """Test the constructor."""
        assert aset.identifier == "SBLGNT-LEB-manual"
        assert aset.sourcedatapath == SOURCES
        assert aset.canon == "nt"

    def test_canon(self) -> None:
        """Test the canon property."""
        wlc = AlignmentSet(
            sourceid="WLC",
            targetid="LEB",
            targetlanguage="eng",
            langdatapath=ENGLANGDATAPATH,
            alternateid="manual",
        )
        assert wlc.canon == "ot"
        # # Bogus source ID
        # now checking in AlignmentSet so this doesn't happen
        # nunya = AlignmentSet(
        #     sourceid="NUNYA", targetid="LEB", targetlanguage="eng", langdatapath=ENGLANGDATAPATH, alternateid="manual"
        # )
        # assert nunya.canon == "X"

    def test_sourceid(self) -> None:
        """Test the constructor with various id values."""
        with pytest.raises(ValueError):
            AlignmentSet(sourceid="SBLGNT!", targetid="LEB", targetlanguage="eng")
        with pytest.raises(ValueError):
            AlignmentSet(sourceid="SBL-GNT", targetid="LEB", targetlanguage="eng")
        with pytest.raises(ValueError):
            AlignmentSet(sourceid="SBL.GNT", targetid="LEB", targetlanguage="eng")

    def test_paths(self, aset: AlignmentSet) -> None:
        """Test the source, target, alignment, and TOML paths."""
        assert aset.sourcepath == SOURCES / "SBLGNT.tsv"
        assert aset.targetpath == ENGLANGDATAPATH / "targets/LEB/nt_LEB.tsv"
        # assert aset.langtargetdirpath == DATAPATH / "alignments/eng/LEB"
        assert aset.alignmentpath == ENGLANGDATAPATH / "alignments/LEB/SBLGNT-LEB-manual.json"
        assert aset.tomlpath == ENGLANGDATAPATH / "alignments/LEB/SBLGNT-LEB-manual.toml"

    # not needed for Alignments
    # def test_comparable(
    #     self, aset: AlignmentSet, asetinternal: AlignmentSet, asethin: AlignmentSet
    # ) -> None:
    #     """Test comparable()."""
    #     assert aset.comparable(asetinternal) is True
    #     assert aset.comparable(asethin) is False
    #     with pytest.raises(AssertionError):
    #         assert aset.comparable("Not an alignment set.")


# not needed for Alignments
# class TestAlignmentSetInternal:
#     """Test the AlignmentSet class for legacy internal structure."""

#     # should also test X value for not nt or ot

#     def test_paths(self, asetinternal: AlignmentSet) -> None:
#         """Test the source, target, alignment, and TOML paths."""
#         assert asetinternal.targetpath == DATAPATH / "targets/eng/LEB/nt_LEB.tsv"
#         # assert aset.langtargetdirpath == DATAPATH / "alignments/eng/LEB"
#         assert asetinternal.alignmentpath == DATAPATH / "alignments/eng/LEB/SBLGNT-LEB-manual.json"
#         assert asetinternal.tomlpath == DATAPATH / "alignments/eng/LEB/SBLGNT-LEB-manual.toml"


class TestAlignmentSetHin:
    """Test the AlignmentSet class for Hindi."""

    def test_init(self, asethin: AlignmentSet) -> None:
        """Test the constructor."""
        assert asethin.identifier == "SBLGNT-IRVHin-manual"
        assert asethin.sourcedatapath == SOURCES
        assert asethin.canon == "nt"

    def test_canon(self, asethin: AlignmentSet) -> None:
        """Test the canon property."""
        assert asethin.canon == "nt"
        # should also test X value for not nt or ot

    def test_paths(self, asethin: AlignmentSet) -> None:
        """Test the source, target, alignment, and TOML paths."""
        assert asethin.sourcepath == SOURCES / "SBLGNT.tsv"
        assert asethin.targetpath == HINLANGDATAPATH / "targets/IRVHin/nt_IRVHin.tsv"
        # assert asethin.langtargetdirpath == DATAPATH / "alignments/IRVHin"
        assert (
            asethin.alignmentpath == HINLANGDATAPATH / "alignments/IRVHin/SBLGNT-IRVHin-manual.json"
        )
        assert asethin.tomlpath == HINLANGDATAPATH / "alignments/IRVHin/SBLGNT-IRVHin-manual.toml"
