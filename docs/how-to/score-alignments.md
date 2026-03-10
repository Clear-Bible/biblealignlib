# How to Score Alignments Against a Reference

Scoring measures how closely an automated alignment matches a manually curated gold standard, using precision, recall, F1, and AER (Alignment Error Rate).

## Score All Verses with ScoreCondition

`ScoreCondition` is the easiest entry point — it derives file paths from named parameters:

```python
from biblealignlib.autoalign.scorer import ScoreCondition

sc = ScoreCondition(
    targetlang="eng",
    targetid="BSB",
    condition="20241220_eflomal_text",   # hypothesis identifier
    sourceid="SBLGNT",
)

result = sc.score_all()
print(result.summary())
# AER: 0.213  F1: 0.787  Precision: 0.787  Recall: 0.787
```

## Score a Single Verse

```python
verse_score = sc.score_verse("41004003")
if verse_score:
    print(verse_score.summary())
```

## Score a Verse Range

```python
score = sc.score_partial(startbcv="41001001", endbcv="41016020")
print(score.summary())   # Mark only
```

## Score Content Words Only

Pass `essential=True` to restrict scoring to nouns, verbs, adjectives, and adverbs:

```python
essential_score = sc.score_all(essential=True)
print(essential_score.summary())
```

## Inspect a Verse as a DataFrame

`verse_dataframe()` returns a matrix showing where the reference and hypothesis agree or disagree:

```python
df = sc.verse_dataframe(
    "41004003",
    truepos="R-H",     # both reference and hypothesis aligned
    falseneg="R--",    # reference aligned, hypothesis missed
    falsepos="--H",    # hypothesis aligned, not in reference
    trueneg="   ",     # neither aligned
    srcattr="text",    # use source text as row labels
)
display(df)
```

## Build a Scorer Directly

For more control, construct a `Scorer` explicitly:

```python
from biblealignlib.autoalign.scorer import Scorer
from biblealignlib.burrito import AlignmentSet, CLEARROOT

referenceset = AlignmentSet(
    sourceid="SBLGNT",
    targetid="BSB",
    targetlanguage="eng",
    langdatapath=CLEARROOT / "Alignments/data/eng",
    alternateid="manual",
)

scorer = Scorer(
    referenceset=referenceset,
    hypothesispath=CLEARROOT / "autoalignment/data/eng/BSB/",
    hypothesisaltid="eflomal_text",
)

result = scorer.score_all()
print(result.summary_dict())
# {"AER": "0.213", "F1": "0.787", "Precision": "0.787", "Recall": "0.787"}
```

## Log Results

```python
sc.log_score(result.summary_dict(), comment="v2 eflomal run")
```

Results are appended to a log file for tracking experiment history.

## Understanding the Metrics

| Metric | Formula | What it measures |
|--------|---------|-----------------|
| Precision | TP / (TP + FP) | How many hypothesis alignments are correct |
| Recall | TP / (TP + FN) | How many reference alignments were found |
| F1 | 2·P·R / (P + R) | Harmonic mean; overall accuracy |
| AER | 1 − Precision | Error rate; lower is better |

A true positive is a `(source_id, target_id)` pair present in both the reference and hypothesis.
