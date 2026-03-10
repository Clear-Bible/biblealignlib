# How to Search Alignments

## Find All Alignments for a Greek/Hebrew Term

Use `Manager.token_alignments()` to search for records by text, lemma, Strong's number, or any other token attribute.

```python
# All records where source text is "Ἰησοῦς"
records = mgr.token_alignments("Ἰησοῦς", role="source", tokenattr="text")

# All records where source lemma is "ἀκούω"
records = mgr.token_alignments("ἀκούω", role="source", tokenattr="lemma")

# Case-insensitive search on target text
records = mgr.token_alignments("love", role="target", tokenattr="text", lowercase=True)
```

Display a record:

```python
for rec in records[:5]:
    print(mgr.display_record(rec))
```

## Search by Strong's Number

```python
records = mgr.token_alignments("G0191", role="source", tokenattr="strong")
print(f"Found {len(records)} alignments for G0191 (ἀκούω)")
```

## Find All Target Translations for a Source Lemma

Combine `token_alignments()` with `VerseData.get_pairs()` to see what English words a Greek lemma maps to:

```python
import collections

lemma = "ἀγάπη"
records = mgr.token_alignments(lemma, role="source", tokenattr="lemma")

translations: collections.Counter = collections.Counter()
for rec in records:
    bcv = rec.source_bcv
    vd = mgr[bcv]
    for src, tgt in vd.get_pairs():
        if src.lemma == lemma:
            translations[tgt.text] += 1

print(translations.most_common(10))
```

## Look Up a Source Token Directly

```python
# By BCVWPID (book-chapter-verse-word)
token = mgr.sourceitems["41004003001"]   # Mark 4:3 word 1
print(token.text, token.lemma, token.gloss)
```

## Find All Alignments for a Verse

```python
vd = mgr["41004003"]   # Mark 4:3

# Iterate over all alignment groups
for src_tokens, tgt_tokens in vd.alignments:
    src_texts = " ".join(t.text for t in src_tokens)
    tgt_texts = " ".join(t.text for t in tgt_tokens)
    print(f"{src_texts:30} → {tgt_texts}")
```

## Find Unaligned Tokens in a Verse

```python
vd = mgr["41004003"]

unaligned_src = vd.unaligned_sources
unaligned_tgt = vd.unaligned_targets

print(f"Unaligned source tokens: {[t.text for t in unaligned_src]}")
print(f"Unaligned target tokens: {[t.text for t in unaligned_tgt]}")
```

## Get a Source-to-Targets Mapping

```python
# For a whole verse
source_targets = vd.get_source_targets()
for src, tgts in source_targets.items():
    tgt_texts = " ".join(t.text for t in tgts)
    print(f"{src.text:20} → {tgt_texts}")

# For one specific source token
token = mgr.sourceitems["41004003006"]
tgts = vd.get_source_alignments(token)
print([t.text for t in tgts])
```
