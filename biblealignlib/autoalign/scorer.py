"""Score hypothesized alignments against gold standard data.

>>> from biblealignlib.burrito import CLEARROOT, AlignmentSet
>>> from biblealignlib.autoalign import scorer

# the easy way: this bundles up these various steps into one scoring
# condition but makes more assumptions
> sc = scorer.ScoreCondition(targetlang="eng", targetid="BSB", condition="20241220_text")
# see ScoreCondition for the individual steps

# score a single verse
>>> bcv = "41004004"
>>> sc.score_verse(bcv)
<VerseScore: 41004004>
>>> print(sc.score_verse(bcv).summary())
41004004: AER=0.2941	P=0.7059	R=0.6667	F1=0.6857
# score a group of verses: here, MRK 4. Any prefix of a BCV works.
>>> print(sc.score_group("41004").summary())
41004: AER=0.2363	P=0.7637	R=0.5016	F1=0.6055
# score all the verses
>>> print(sc.score_all().summary())
all: AER=0.1864	P=0.8136	R=0.5352	F1=0.6456
# score all the verses, essential only
>>> print(sc.score_all(essential=True).summary())
all: AER=0.1424	P=0.8576	R=0.4925	F1=0.6257
# score only MAT-LUK
>>> sc.score_partial(startbcv="40001001", endbcv="42024053").summary_dict()

# log the summary from a score
>>> sc.log_score(summary_dict=sc.score_all().summary_dict(), comment="include distinguishing conditions")

# score and log the four base conditions with lots of assumptions
>>> scorer.ScoreBaseConditions(targetlang="tpi", targetid="TPB08", conditionbase="20241224eflomal")

# the longer way
"""

import copy
from csv import DictWriter
import os
from pathlib import Path

# from statistics import mean
from typing import Optional

import pandas as pd

import biblealignlib as bal
from biblealignlib.burrito import (
    AlignmentRecord,
    AlignmentSet,
    AlignmentsReader,
    Manager,
    Source,
    Target,
    util,
)
from biblealignlib.burrito.util import groupby_bcv

from .Score import EssentialVerseScore, GroupScore, VerseScore


## Might want to separate out reading and writing: conflating them
## makes this code more complex
class Scorer(Manager):
    """Map the verses of a corpus to CorpusMapping instances.

    On initialization, loads existing data. read_pharaoh() then
    returns a new AlignmentGroup for the output of an automated
    algorithm.

    """

    def __init__(
        self,
        referenceset: AlignmentSet,
        hypothesispath: Path,
        hypothesisaltid: str,
        creator: str = "GrapeCity",
    ):
        """Initialize the PharaohMapper."""
        self.hypothesispath = hypothesispath
        self.hypothesisaltid = hypothesisaltid
        self.condition = self.hypothesispath.parent.name
        self.hypothesisset = copy.copy(referenceset)
        self.hypothesisset.alignmentpath = hypothesispath
        assert (
            self.hypothesisset.alignmentpath.exists()
        ), f"No such alignment path: {self.hypothesisset.alignmentpath}"
        self.hypothesisset.alternateid = hypothesisaltid
        # does not reset sourcepath, targetpath,  tomlpath
        super().__init__(alignmentset=referenceset, creator=creator)
        self.referenceset = referenceset
        # capture to keep distinct from hypreader
        self.refreader = self.alignmentsreader
        print(f"----- Hypothesis data: {self.hypothesisset}")
        print(self.hypothesisset.displaystr)
        self.hypreader: AlignmentsReader = AlignmentsReader(
            alignmentset=self.hypothesisset,
        )
        self.hypreader.clean_alignments(self.sourceitems, self.targetitems)
        # group records by BCV
        self.bcv["hyprecords"]: dict[str, AlignmentRecord] = groupby_bcv(
            list(self.hypreader.alignmentgroup.records), lambda r: r.source_bcv
        )
        # and make VerseData instances
        self.bcv["hypversedata"] = {
            bcvid: self.make_versedata(bcvid, self.bcv["hyprecords"])
            for bcvid in self.bcv["hyprecords"]
        }
        self.exptargetdir = referenceset.langdatapath.parent / f"exp/{referenceset.targetid}"
        self.scorelogfile = self.exptargetdir / "scorelog.tsv"

    @property
    def refrecords(self) -> list[AlignmentRecord]:
        """Return a list of the reference alignment records."""
        return self.refreader.alignmentgroup.records

    @property
    def hyprecords(self) -> list[AlignmentRecord]:
        """Return a list of the hypothesis alignment records."""
        return self.hypreader.alignmentgroup.records

    def score_verse(self, bcvid: str, essential: bool = False) -> Optional[VerseScore]:
        """Return a VerseScore instance for a BCV reference.

        With essential=True (default is false), only score alignments
        where all of the source tokens have noun, verb, adjective,
        adverb as part-of-speech ('essential-full').

        """
        scorefn = EssentialVerseScore if essential else VerseScore
        if (bcvid in self.bcv["versedata"]) and (bcvid in self.bcv["hypversedata"]):
            return scorefn(
                reference=self.bcv["versedata"][bcvid], hypothesis=self.bcv["hypversedata"][bcvid]
            )
        else:
            return None

    def _score_verses(self, bcvs: list[str], essential: bool = False) -> list[VerseScore]:
        """Return VerseScore instances for a list of bcv identifier."""
        return [
            score for bcv in bcvs if (score := self.score_verse(bcv, essential=essential)) if score
        ]

    def score_group(self, identifier: str, essential: bool = False) -> GroupScore:
        """Score a group of verses with a shared initial identifier string."""
        return GroupScore(
            identifier=identifier,
            verse_scores=self._score_verses(
                [bcv for bcv in self if bcv.startswith(identifier)], essential=essential
            ),
        )

    def score_partial(self, startbcv: str, endbcv: str, essential: bool = False) -> GroupScore:
        """Score a group of verses defined by start/endbcv."""
        partial: list[str] = util.filter_by_bcv(self.keys(), startbcv=startbcv, endbcv=endbcv)
        return GroupScore(
            identifier=f"{startbcv}-{endbcv}",
            verse_scores=self._score_verses(
                [bcv for bcv in partial],
                essential=essential,
            ),
        )

    def score_all(self, essential: bool = False) -> None:
        """Score all verses."""
        # verse_scores = [self.score_verse(bcv) for bcv in self]
        return GroupScore(
            identifier="all",
            verse_scores=self._score_verses(self.keys(), essential=essential),
        )

    def log_score(self, summary_dict: dict[str, str], comment: str = "") -> None:
        """Log the summary dict from a score.

        You should use comment to indicate what was being scored,
        including whether essential, partial, etc.

        """
        assert "AER" in summary_dict, f"No 'AER' key: is this a summary dict? {summary_dict}"
        fieldnames = ("Condition", "AER", "F1", "Precision", "Recall", "Comment")
        # ensure the file exists
        self.scorelogfile.touch()
        # write a header if empty
        if os.stat(self.scorelogfile).st_size == 0:
            with self.scorelogfile.open("w", newline="") as f:
                writer = DictWriter(f, fieldnames=fieldnames, delimiter="\t")
                writer.writeheader()
        # could check here to see if a score for condition already
        # exists, but that seems like overkill
        with self.scorelogfile.open("a") as f:
            scoredict = summary_dict.copy()
            scoredict["Condition"] = self.condition
            scoredict["Comment"] = comment
            writer = DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writerow(scoredict)

    def verse_dataframe(
        self,
        bcv: str,
        truepos: str = "R-H",
        falseneg: str = "R--",
        falsepos: str = "--H",
        trueneg: str = "   ",
        srcattr: str = "text",
    ) -> pd.DataFrame:
        """Return a dataframe showing ref and hyp values.

        Displays target terms for column names, and source terms for
        index.

        Markers:
        * R-H indicates a reference and hypothesis hit (true positive)
        * R-- indicates a reference hit but no hypothesis hit (false negative)
        * --H indicates a hypothesis hit but no reference hit (false positive)
        * no mark indicates a true negative

        """

        def get_mark(src: Source, trg: Target) -> str:
            refhit = src in alignments["ref"].get(trg, {})
            hyphit = src in alignments["hyp"].get(trg, {})
            if refhit and hyphit:
                return truepos
            elif refhit and not hyphit:
                return falseneg
            elif hyphit and not refhit:
                return falsepos
            else:
                return trueneg

        refvd = self.bcv["versedata"][bcv]
        hypvd = self.bcv["hypversedata"][bcv]
        # should be the same for both
        sources = refvd.sources
        # maps Target instances to displayable text: should be the same for both
        target_text = dict(zip(refvd.targets_included, refvd.get_texts(unique=True)))
        # dict mapping each target instance to aligned source instances
        alignments = {
            "ref": {trg: alpair[0] for alpair in refvd.alignments for trg in alpair[1]},
            "hyp": {trg: alpair[0] for alpair in hypvd.alignments for trg in alpair[1]},
        }
        # are there duplicates here? possibly
        # dict mapping
        dfdata = {
            textdisplay: [get_mark(src, trg) for src in sources]
            for (trg, textdisplay) in target_text.items()
        }
        return pd.DataFrame(dfdata, index=[getattr(src, srcattr) for src in sources])


# this may be a weird overload
class ScoreCondition(Scorer):
    """Bundle up parameters for scoring."""

    def __init__(
        self,
        targetlang: str,
        targetid: str,
        # the directory name where hypothesis data is found
        condition: str,
        sourceid: str = "SBLGNT",
        # altid for alignment json
        hypothesisaltid: str = "eflomal",
    ) -> None:
        """Initialize an instance."""
        self.alsetref = AlignmentSet(
            targetlanguage=targetlang,
            targetid=targetid,
            sourceid=sourceid,
            langdatapath=(bal.CLEARROOT / f"alignments-{targetlang}/data"),
        )
        self.conditiondir = self.alsetref.langdatapath.parent / f"exp/{targetid}/{condition}"
        assert self.conditiondir.exists(), f"conditiondir does not exist: {self.conditiondir}"
        super().__init__(
            referenceset=self.alsetref,
            hypothesispath=(self.conditiondir / f"{sourceid}-{targetid}-{hypothesisaltid}.json"),
            hypothesisaltid=hypothesisaltid,
        )


class ScoreBaseConditions:
    """Score text and lemma, full and essential, and log results.

    Lots of implicit assumptions here.
    """

    def __init__(
        self,
        targetlang: str,
        targetid: str,
        # the base of the directory name where hypothesis data is found
        # assumes "_text" and "_lemma" suffixes
        conditionbase: str,
        sourceid: str = "SBLGNT",
        # altid for alignment json
        hypothesisaltid: str = "eflomal",
    ) -> None:
        """Initialize an instance."""
        for input in ("text", "lemma"):
            sc = ScoreCondition(
                targetlang=targetlang, targetid=targetid, condition=f"{conditionbase}_{input}"
            )
            sc.log_score(
                summary_dict=sc.score_all(essential=False).summary_dict(), comment=f"full_{input}"
            )
            sc.log_score(
                summary_dict=sc.score_all(essential=True).summary_dict(), comment=f"ess_{input}"
            )
        print(f"Scores logged to {sc.scorelogfile}")
