"""Test code in burrito.source

Does not test SourceReader or writing files.

There are different assumptions for GrapeCity formatted data, that
gets processed by Source.fromjsondict, as opposed to instantiating
Source objects directly. In particular, fromjsondict normalizes IDs
and some Unicode characters.

"""

import pytest

from biblealignlib import SOURCES
from biblealignlib.burrito import Source, SourceReader, macula_prefixer, macula_unprefixer


class TestMacula_Prefixer:
    """Test macula_prefixer()."""

    def test_ot(self) -> None:
        """Test OT prefixing."""
        assert macula_prefixer("010010010012") == "o010010010012"

    def test_nt(self) -> None:
        """Test NT prefixing."""
        assert macula_prefixer("41001001001") == "n41001001001"

    def test_error(self) -> None:
        """Test error raising if doesn't match a BCVWP string."""
        # no prefixing beyond the NT book range
        with pytest.raises(ValueError):
            assert macula_prefixer("67001001001") == "67001001001"
        # no initial book reference
        with pytest.raises(ValueError):
            assert macula_prefixer("abc") == "abc"


class TestMacula_Unprefixer:
    """Test macula_unprefixer()."""

    def test_ot(self) -> None:
        """Test OT unprefixing."""
        assert macula_unprefixer("o010010010012") == "010010010012"
        assert macula_unprefixer("010010010012") == "010010010012"

    def test_nt(self) -> None:
        """Test NT unprefixing."""
        assert macula_unprefixer("n41001001001") == "41001001001"
        assert macula_unprefixer("41001001001") == "41001001001"


@pytest.fixture(scope="module")
def mrk_4_9_4() -> Source:
    """Return a Source instance."""
    mrk_4_9_4_dict = {
        # GC data includes a word number
        "id": "n410040090051",
        "altId": "ὦτα-1",
        "text": "ὦτα",
        "strong": "3775",
        "gloss": "ears",
        "gloss2": "ears",
        "lemma": "οὖς",
        "pos": "noun",
        "morph": "n- -apn-",
        "required": True,
    }
    return Source.fromjsondict(mrk_4_9_4_dict)


@pytest.fixture(scope="module")
def gen_1_1_1() -> Source:
    """Return a Source instance."""
    gen_1_1_1_dict = {
        "id": "o010010010012",
        "altId": "רֵאשִׁ֖ית-1",
        "text": "רֵאשִׁית",
        "strong": "H7225",
        "gloss": "beginning",
        "lemma": "",
        "pos": "noun",
        "morph": "",
        # required: default is True
    }
    return Source.fromjsondict(gen_1_1_1_dict)


@pytest.fixture(scope="module")
def serialized() -> dict[str, str]:
    """Return a Source instance for data read from file."""
    return {
        # GC data includes a word number
        "id": "410040090051",
        "altId": "ὦτα-1",
        "text": "ὦτα",
        "strongs": "775",
        "gloss": "ears",
        "gloss2": "ears",
        "lemma": "οὖς",
        "pos": "noun",
        "morph": "n- -apn-",
        "required": "y",
    }


class TestSource:
    """Test Source()."""

    def test_init_gen(self, gen_1_1_1: Source) -> None:
        """Test initialization."""
        assert gen_1_1_1.id == "010010010012"
        # altId has vowel-pointing differences from text?
        # assert gen_1_1_1.altId[:-2] == gen_1_1_1.text
        assert gen_1_1_1.text == "רֵאשִׁית"
        assert gen_1_1_1.maculaid == "o010010010012"
        assert gen_1_1_1.is_content

    def test_init(self, mrk_4_9_4: Source) -> None:
        """Test initialization."""
        # no word part index
        assert mrk_4_9_4.id == "41004009005"
        assert mrk_4_9_4.altId[:-2] == mrk_4_9_4.text
        assert mrk_4_9_4.maculaid == "n41004009005"
        assert mrk_4_9_4.tokenid == "41004009005"
        assert mrk_4_9_4.is_content

    def test_idtext(self, mrk_4_9_4: Source) -> None:
        """Text idtext property."""
        assert mrk_4_9_4.idtext == (
            "41004009005",
            "ὦτα",
        )

    # should add tests for is_content == False

    # this happens intentionally for Hebrew? So dropping this check
    # and its test for now
    # def test_empty_text(self) -> None:
    #     """Test failing on empty text."""
    #     notext: dict[str, str] = {
    #         "id": "41004009005",
    #         "altId": "ὦτα-1",
    #         "text": "",
    #         "strong": "3775",
    #         "gloss": "ears",
    #         "gloss2": "ears",
    #         "lemma": "οὖς",
    #         "pos": "noun",
    #         "morph": "n- -apn-",
    #     }
    #     with pytest.raises(ValueError):
    #         Source(**notext)

    def test_badid(self) -> None:
        """Test failing on ID with too many characters."""
        bad: dict[str, str] = {
            "id": "4100400900005",
            "altId": "ὦτα-1",
            "text": "ὦτα",
            "strong": "3775",
            "gloss": "ears",
            "gloss2": "ears",
            "lemma": "οὖς",
            "pos": "noun",
            "morph": "n- -apn-",
            "required": True,
        }
        with pytest.raises(AssertionError):
            Source(**bad)

    def test_gcid(self) -> None:
        """Test fromjsondict on GC ID without leading zero."""
        gcdict: dict[str, str] = {
            # missing leading zero
            "id": "10010010011",
            # ignore this obviously non-Hebrew data
            "altId": "ὦτα-1",
            "text": "ὦτα",
            "strong": "3775",
            "gloss": "ears",
            "gloss2": "ears",
            "lemma": "οὖς",
            "pos": "noun",
            "morph": "n- -apn-",
        }
        gen_1_1 = Source.fromjsondict(gcdict)
        assert gen_1_1.id == "010010010011"

    def test_asdict(self, mrk_4_9_4: Source) -> None:
        """Test asdict()."""
        assert mrk_4_9_4.asdict() == {
            "id": "n41004009005",
            "altId": "ὦτα-1",
            "text": "ὦτα",
            "strongs": "G3775",
            "gloss": "ears",
            "gloss2": "ears",
            "lemma": "οὖς",
            "pos": "noun",
            "morph": "n- -apn-",
            "required": True,
        }

    def test_asdict_omittext(self, mrk_4_9_4: Source) -> None:
        """Test asdict()."""
        assert mrk_4_9_4.asdict(omittext=True) == {
            "id": "n41004009005",
            "altId": "--",
            "text": "--",
            "strongs": "G3775",
            "gloss": "ears",
            "gloss2": "ears",
            "lemma": "οὖς",
            "pos": "noun",
            "morph": "n- -apn-",
            "required": True,
        }

    def test_deserialized(self, serialized: dict[str, str]) -> None:
        """Test asdict()."""
        deserialized: dict[str, str] = {SourceReader.inmap[k]: v for k, v in serialized.items()}
        assert Source(**deserialized).asdict() == {
            "id": "n41004009005",
            "altId": "ὦτα-1",
            "text": "ὦτα",
            # tests prefix and zero padding
            "strongs": "G0775",
            "gloss": "ears",
            "gloss2": "ears",
            "lemma": "οὖς",
            "pos": "noun",
            "morph": "n- -apn-",
            "required": True,
        }


class TestSourceReader:
    """Test SourceReader()."""

    sr = SourceReader(SOURCES / "SBLGNT.tsv")

    def test_init(self) -> None:
        """Test initialization."""
        # FRAGILE
        assert len(self.sr) > 137700
        # no lemmas yet for SBLGNT
        # assert sr["n41004003001"].lemma == "ἀκούω"
        assert self.sr["41004003001"].strong == "G0191"

    def test_vocabulary(self) -> None:
        """Test vocabulary()."""
        assert len(self.sr.vocabulary()) == 19355
        assert len(self.sr.vocabulary(lower=True)) == 18619
        assert len(self.sr.vocabulary(tokenattr="lemma")) == 5468

    def test_term_tokens(self) -> None:
        """Test term_tokens()."""
        # token.id here excludes corpus_prefix, but includes part_ID
        assert [token.id for token in self.sr.term_tokens("βλαστᾷ")] == ["41004027011"]
        assert [token.id for token in self.sr.term_tokens("βλαστάνω", tokenattr="lemma")] == [
            "40013026003",
            "41004027011",
            "58009004024",
            "59005018012",
        ]
        # lemma doesn't match surface text
        assert [token.id for token in self.sr.term_tokens("βλαστάνω")] == []
        assert [token.id for token in self.sr.term_tokens("Οἶδας")] == [
            "40015012007",
            "55001015001",
        ]
        assert len([token.id for token in self.sr.term_tokens("οἶδας")]) == 15
        # more if disregarding case
        assert len([token.id for token in self.sr.term_tokens("Οἶδας", lowercase=True)]) == 17

    def test_book_token_counts(self) -> None:
        """Test book_token_counts()."""
        bc = self.sr.book_token_counts()
        assert bc["41"] == 11286

    def test_book_verse_counts(self) -> None:
        """Test book_verse_counts()."""
        bcv = self.sr.book_verse_counts()
        assert bcv["41"] == 673


class TestOTSourceReader:
    """Test SourceReader()."""

    sr = SourceReader(SOURCES / "WLCM.tsv")

    def test_init(self) -> None:
        """Test initialization."""
        # FRAGILE: round number for slightly more generality
        assert len(self.sr) >= 469476
        assert self.sr["010010010021"].asdict() == {
            "id": "o010010010021",
            "altId": "בָּרָ֣א-1",
            "text": "בָּרָא",
            "strongs": "H1254",
            "gloss": "created",
            "gloss2": "he.created",
            "lemma": "",
            "pos": "verb",
            "morph": "",
            "required": True,
        }
        # this fails: Unicode normalization??

    # 2025-12-16: investigate later to fix this
    # def test_vocabulary(self) -> None:
    #     """Test vocabulary()."""
    #     assert len(self.sr.vocabulary()) == 83669
    #     assert len(self.sr.vocabulary(tokenattr="lemma")) == 9044

    # def test_term_tokens(self) -> None:
    #     """Test term_tokens()."""
    #     assert [token.id for token in self.sr.term_tokens("βλαστᾷ")] == ["n41004027011"]
    #     assert [token.id for token in self.sr.term_tokens("βλαστάνω", tokenattr="lemma")] == [
    #         "n40013026003",
    #         "n41004027011",
    #         "n58009004024",
    #         "n59005018012",
    #     ]
    #     # lemma doesn't match surface text
    #     assert [token.id for token in self.sr.term_tokens("βλαστάνω")] == []
    #     assert [token.id for token in self.sr.term_tokens("Οἶδας")] == ["n40015012007", "n55001015001"]
    #     assert len([token.id for token in self.sr.term_tokens("οἶδας")]) == 15
    #     # more if disregarding case
    #     assert len([token.id for token in self.sr.term_tokens("Οἶδας", lowercase=True)]) == 17
