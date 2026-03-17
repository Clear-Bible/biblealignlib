"""Split TSV files into OT and NT files.

# assume you first copy the kathairo file to the appropriate language-specific repository
>>> from biblealignlib import CLEARROOT
>>> from biblealignlib.util.canonsplit import CanonSplit
>>> LANGDATAPATH = CLEARROOT / "alignments-rus/data"
>>> targetid = "RUSSYN"
>>> targetpath = LANGDATAPATH / f"targets/{targetid}"
>>> cs = CanonSplit(targetpath / f"target_{targetid}_20240610.tsv", targetpath / f"ot_{targetid}.tsv", targetpath / f"nt_{targetid}.tsv")
>>> cs.split()

Command line example:
# cd alignments-eng/data/targets/eng/BSB
$ poetry run python -m biblealignlib.util.canonsplit BSB_english_20240610.tsv ot_BSB-20240610.tsv nt_BSB-20240610.tsv

"""

import argparse
import csv
from pathlib import Path
import re


class CanonSplit:
    def __init__(self, inputFilePath: Path, otFilePath: Path, ntFilePath: Path) -> None:
        self.inputFilePath = inputFilePath
        assert self.inputFilePath.exists(), f"Input path does not exist: {self.inputFilePath}"
        self.otFilePath = otFilePath
        self.ntFilePath = ntFilePath
        self.otcanonre = re.compile(r"^[0-3][0-9]")
        self.ntcanonre = re.compile(r"^[4-6][0-9]")
        # don't include 67-69
        self.notntcanonre = re.compile(r"^6[7-9]")

    def _is_ot(self, idstr: str) -> bool:
        """Return True if the id is in the OT."""
        return bool(self.otcanonre.match(idstr))

    def _is_nt(self, idstr: str) -> bool:
        """Return True if the id is in the NT."""
        return bool(self.ntcanonre.match(idstr) and not self.notntcanonre.match(idstr))

    def split(self) -> None:
        """Split input into OT and NT files based on ids."""
        with self.inputFilePath.open("r") as file:
            reader = csv.reader(file, delimiter="\t")
            with self.otFilePath.open("w") as otFile:
                with self.ntFilePath.open("w") as ntFile:
                    for row in reader:
                        if row[0].startswith("id"):
                            otFile.write("\t".join(row) + "\n")
                            ntFile.write("\t".join(row) + "\n")
                        elif self._is_ot(row[0]):
                            otFile.write("\t".join(row) + "\n")
                        elif self._is_nt(row[0]):
                            ntFile.write("\t".join(row) + "\n")
                        else:
                            raise ValueError(f"Invalid id value: {row[0]}")


def main() -> None:
    """Call CanonSplit from the command line"""
    parser = argparse.ArgumentParser(
        description="Split a Bible text file into OT and NT files based on ids."
    )
    parser.add_argument("inputFilePath", type=Path, help="Path to the input file.")
    parser.add_argument("otFilePath", type=Path, help="Path to the output OT file.")
    parser.add_argument("ntFilePath", type=Path, help="Path to the output NT file.")

    args = parser.parse_args()

    splitter = CanonSplit(args.inputFilePath, args.otFilePath, args.ntFilePath)
    splitter.split()


if __name__ == "__main__":
    main()
