"""Manage a set of alignment data.

This requires setting a number of parameters.

>>> from biblealignlib.burrito import CLEARROOT, AlignmentSet
# your local copy of alignments-eng/data
>>> ENGLANGDATAPATH = CLEARROOT / "alignments-eng/data"
>>> asetleb = AlignmentSet(sourceid="SBLGNT", targetid="LEB",
                           targetlanguage="eng", langdatapath=ENGLANGDATAPATH,
                           alternateid="manual")
>>> asetleb.identifier
'SBLGNT-LEB-manual'
>>> asetleb.canon
'nt'
>>> asetleb.sourcedatapath
PosixPath('/Users/sboisen/git/Clear-Bible/internal-Alignments/data/sources')
>>> asetleb.targetpath
PosixPath('/Users/sboisen/git/Clear-Bible/alignments-eng/data/targets/LEB/nt_LEB.tsv')
>>> asetleb.alignmentpath
PosixPath('/Users/sboisen/git/Clear-Bible/alignments-eng/data/alignments/LEB/SBLGNT-LEB-manual.json')
>>> asetleb.tomlpath
PosixPath('/Users/sboisen/git/Clear-Bible/alignments-eng/data/alignments/LEB/SBLGNT-LEB-manual.toml')
>>> asetleb.check_files()
True

"""

from dataclasses import dataclass
from pathlib import Path
import re

from biblealignlib import CLEARROOT, SourceidEnum


@dataclass
class AlignmentSet:
    """Manage a set of files for an alignment."""

    # this should become an enumerated set
    sourceid: str
    targetid: str
    # an ISO 639-3 code (not a full name)
    targetlanguage: str
    # use the published source, not internal
    sourcedatapath: Path = CLEARROOT / "Alignments/data/sources"
    # language-specific data path, like alignments-hin/data, or
    # published in alignments/data/{lang}
    langdatapath: Path = Path()
    # most common default, but override if necessary
    alternateid: str = "manual"
    reponame: str = ""
    # these are computed in post-init
    sourcepath: Path = Path()
    targetpath: Path = Path()
    alignmentpath: Path = Path()
    tomlpath: Path = Path()

    def __post_init__(self) -> None:
        """Post-initialization checks."""
        for idattr in ["sourceid", "targetid"]:
            idstr = getattr(self, idattr)
            # only allow ASCII letters, digits, and underscores
            if not re.fullmatch(r"\w+", idstr, flags=re.ASCII):
                raise ValueError(f"Invalid {idattr}: {idstr}")
        # make sure source id is recognized
        _ = SourceidEnum(self.sourceid)
        if self.alternateid and not re.fullmatch(r"\w+", self.alternateid, flags=re.ASCII):
            raise ValueError(f"Invalid alternateid: {self.alternateid}")
        self.sourcepath = self.sourcedatapath / f"{self.sourceid}.tsv"
        self.targetpath = (
            self.langdatapath / f"targets/{self.targetid}/{self.canon}_{self.targetid}.tsv"
        )
        assert self.targetpath.exists(), f"No such target TSV: {self.targetpath}"
        self.alignmentpath = (
            self.langdatapath / f"alignments/{self.targetid}/{self.identifier}.json"
        )
        assert self.alignmentpath.exists(), f"No such alignment path: {self.alignmentpath}"
        self.tomlpath = self.langdatapath / f"alignments/{self.targetid}/{self.identifier}.toml"
        # don't require this for loading data, only for publishing
        # assert self.tomlpath.exists(), f"No such TOML file: {self.tomlpath}"

    def __repr__(self) -> str:
        """Return a printed representation."""
        return f"<AlignmentSet: {self.targetlanguage}, {self.identifier}>"

    def __hash__(self) -> int:
        """Return a hash key for Source."""
        return hash(self.sourceid + self.targetid + self.alternateid)

    # def from_repo(self, repodatapath: Path) -> None:
    #     """Reset target and alignment paths for repopath.

    #     repopath should be the root of a language-specific alignment
    #     repository (like alignments-arb). This assumes conventional
    #     directory structures.

    #     """
    #     if not repodatapath.exists():
    #         raise ValueError(f"Missing repository path: {repodatapath}")
    #     # this path construction logic is fragile
    #     tpathtail = self.targetpath.relative_to(self.datapath / "targets" / self.targetlanguage)
    #     self.targetpath = (repodatapath / "targets").joinpath(tpathtail)
    #     apathtail = self.alignmentpath.relative_to(self.datapath / "alignments" / self.targetlanguage)
    #     self.alignmentpath = (repodatapath / "alignments").joinpath(apathtail)

    @property
    def identifier(self) -> str:
        """Return a string identifying the set.

        Delimiter is fixed as a hyphen (which is therefore not allowed within identifiers).
        """
        basestr = f"{self.sourceid}-{self.targetid}"
        if self.alternateid:
            basestr += f"-{self.alternateid}"
        return basestr

    # this may now be misleading since data could come from multiple paths
    # @property
    # def langtargetdirpath(self) -> Path:
    #     """Return the path of the language and target folder, relative to datapath."""
    #     return self.datapath / f"alignments/{self.targetlanguage}/{self.targetid}"

    @property
    def canon(self) -> str:
        """Return a string for the source canon: 'nt', 'ot', or 'X'."""
        return SourceidEnum.get_canon(self.sourceid)

    @property
    def displaystr(self) -> str:
        """Return a string displaying configuration information."""
        return f"""
        - sourcepath: {self.sourcepath}
        - targetpath: {self.targetpath}
        - alignmentpath: {self.alignmentpath}
        - tomlpath: {self.tomlpath}
        """

    # not for Alignments
    def comparable(self, other: "AlignmentSet") -> bool:
        """Compare two alignment sets and return True if they can be usefully compared."""

        def compattr(attr) -> bool:
            selfvalue = getattr(self, attr)
            othervalue = getattr(other, attr)
            if selfvalue != othervalue:
                print(f"Different values for {attr}: {selfvalue} vs {othervalue}")
                return False
            else:
                return True

        assert isinstance(other, AlignmentSet), "Comparison must be to another AlignmentSet."
        for attr in ["sourceid", "targetlanguage"]:
            if not compattr(attr):
                return False
        return True

    def check_files(self) -> bool:
        """Check if files exists."""
        pathattrs = ["sourcepath", "targetpath", "alignmentpath", "tomlpath"]
        for pathattr in pathattrs:
            pathval = getattr(self, pathattr)
            if not pathval.exists():
                raise ValueError(f"Missing {pathattr} file: {pathval}")
        return True
