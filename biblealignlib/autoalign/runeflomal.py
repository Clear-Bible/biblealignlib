"""Bundle up several steps into a single function for running eflomal.

THIS WON'T WORK until we get eflomal running in biblealignlib
This assumes the input files for eflomal already exist in
autoalignment/data/{targetlang}/{targetid}: if not, see
biblealignlib.autoalign.writer.PharaohWriter.

"""

from biblealignlib.burrito import CLEARROOT, AlignmentSet
from biblealignlib.autoalign import eflomal


def runeflomal(
    targetlang: str, targetid: str, condition: str, sourceid: str = "SBLGNT", lemma: bool = False
) -> None:
    """Collect parameters to run eflomal, following naming conventions."""
    alsetref = AlignmentSet(
        targetlanguage=targetlang,
        targetid=targetid,
        sourceid=sourceid,
        langdatapath=(CLEARROOT / f"alignments-{targetlang}/data"),
    )
    if lemma:
        condition += "_lemma"
        inputname = f"{sourceid}-{targetid}-lemma.piped.txt"
    else:
        condition += "_text"
        inputname = f"{sourceid}-{targetid}.piped.txt"
    efinst = eflomal.Eflomal(alsetref, condition, inputname=inputname)
    efinst.run_eflomal()
    efinst.run_atools()
