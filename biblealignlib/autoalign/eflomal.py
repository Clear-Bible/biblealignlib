"""Set up parameters and run eflomal-align.

This assumes you've built eflomal-align, and things are located in
their conventional places.

>>> from biblealignlib.burrito import CLEARROOT, AlignmentSet
>>> from biblealignlib.autoalign import eflomal
>>> targetlang, targetid, sourceid = ("eng", "BSB", "SBLGNT")
>>> alsetref = AlignmentSet(targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"))
# set up for output to "test" as experimental condition
>>> efinst = eflomal.Eflomal(alsetref, "test")
# create the forward and reverse output
>>> efinst.run_eflomal()
# create the symmetrized output
>>> efinst.run_atools()

TODO:
- run in Python rather than subprocess
- write log file
- better time stamping?
"""

from datetime import datetime
from pathlib import Path
import subprocess

# import eflomal

from biblealignlib import CLEARROOT

from biblealignlib.burrito import AlignmentSet

class Eflomal:
    # aligner = eflomal.Aligner()
    aligner = "eflomal-align"
    makepriors = "eflomal-makepriors"
    # this needs a way to get built in internal-alignments: this path
    # likely only works for Sean
    atools = CLEARROOT.parent / "clab/fast_align/build/atools"
    autodatapath: Path = CLEARROOT / "autoalignment/data"

    def __init__(self, alignmentset: AlignmentSet, condition: str, inputname: str = "") -> None:
        """Initialize an instance."""
        self.alignmentset = alignmentset
        # self.eflomalpath = ROOT / f".venv/bin/{self.eflomal}"
        if not inputname:
            inputname = f"{self.alignmentset.sourceid}-{self.alignmentset.targetid}.piped.txt"
        self.inputpath = (self.autodatapath /
                          self.alignmentset.targetlanguage /
                          self.alignmentset.targetid / inputname)
        self.expdir = self.alignmentset.langdatapath.parent / "exp" / self.alignmentset.targetid
        self.conditiondir = self.expdir / condition
        self.conditiondir.mkdir(parents=True, exist_ok=True)
        # the standard logger doesn't work well for interactive use: rolling my own
        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.logfilepath = self.conditiondir / f"log_{timestamp}.txt"
        # less transient pharaoh parameters
        self.pharaohpath: Path = self.conditiondir / "pharaoh.txt"
        self.forwardpath: Path = self.conditiondir / "forward.pharaoh.txt"
        self.reversepath: Path = self.conditiondir / "reverse.pharaoh.txt"
        self.priorspath: Path = self.conditiondir / "priors.tsv"


    def log(self, message: str) -> None:
        timestr = datetime.now().isoformat(timespec='minutes')
        print(message)
        with self.logfilepath.open("a") as f:
            f.write(f"{timestr} {message}\n")

    # def run_aligner(self) -> None:
    #     self.aligner.align(
    #         src_input=self
    #     )
    
    def run_eflomal(self, readpriors: bool = False) -> None:
        """Run eflomal-align with parameters in a shell process.

        With readpriors=True (default is False), read priors: this
        assumes you've previously created them with run_makepriors().

        """
        command = [self.aligner, "--overwrite"]
        command += ["--input", str(self.inputpath)]
        command += ["--forward-links", str(self.forwardpath)]
        command += ["--reverse-links", str(self.reversepath)]
        if readpriors:
            command += ["--priors", str(self.priorspath)]
        self.log(f"Command: {command}")
        if not subprocess.run(command):
            self.log("Failed on eflomal")
        return

    def run_makepriors(self) -> None:
        """Run eflomal-makepriors with parameters in a shell process.

        Requires a previous run_eflomal. 
        """
        command = [self.makepriors]
        command += ["--input", str(self.inputpath)]
        # annoying name variance
        command += ["--forward-alignments", str(self.forwardpath)]
        command += ["--reverse-alignments", str(self.reversepath)]
        command += ["--priors", str(self.priorspath)]
        self.log(f"Command: {command}")
        if not subprocess.run(command):
            self.log("Failed on makepriors")
        return

    def run_atools(self) -> None:
        """Run atools with parameters in a shell process."""
        atoolscmd = [self.atools, "-i", self.forwardpath, "-j", self.reversepath,
                     "-c", "grow-diag-final-and"]
        self.log(f"Command: {atoolscmd}")
        with self.pharaohpath.open("w") as f:
            atoolscode = subprocess.run(atoolscmd, stdout=f)
            if not atoolscode:
                self.log("Failed on atools")
        return
