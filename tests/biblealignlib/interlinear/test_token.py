"""Test code in interlinear.token."""

import pytest

from biblealignlib.burrito import Source, Target
from biblealignlib.interlinear.token import AlignedToken


@pytest.fixture(scope="module")
def source_token() -> Source:
    """Return a Source token instance."""
    return Source(
        id="41004003001",
        text="ἀκούετε",
        altId="ἀκούω-1",
        strong="G0191",
        lemma="ἀκούω",
        gloss="hear",
        gloss2="you.hear",
        pos="verb",
        morph="v-2pam--",
    )


@pytest.fixture(scope="module")
def target_token() -> Target:
    """Return a Target token instance."""
    return Target(
        id="41004003002",
        text="Listen",
        source_verse="41004003",
    )


@pytest.fixture(scope="module")
def source_token2() -> Source:
    """Return another Source token instance."""
    return Source(
        id="41004003003",
        text="ἰδού",
        altId="ὁράω-1",
        strong="G3708",
        lemma="ὁράω",
        gloss="behold",
        gloss2="behold",
        pos="interjection",
        morph="",
    )


@pytest.fixture(scope="module")
def target_token2() -> Target:
    """Return another Target token instance."""
    return Target(
        id="41004003004",
        text="Behold",
        source_verse="41004003",
    )


class TestAlignedToken:
    """Test AlignedToken()."""

    def test_init_both_tokens(self, source_token: Source, target_token: Target) -> None:
        """Test initialization with both source and target tokens."""
        at = AlignedToken(targettoken=target_token, sourcetoken=source_token, aligned=True)
        assert at.targettoken == target_token
        assert at.sourcetoken == source_token
        assert at.aligned is True

    def test_init_target_only(self, target_token: Target) -> None:
        """Test initialization with target token only."""
        at = AlignedToken(targettoken=target_token, aligned=False)
        assert at.targettoken == target_token
        assert at.sourcetoken is None
        assert at.aligned is False

    def test_init_source_only(self, source_token: Source) -> None:
        """Test initialization with source token only."""
        at = AlignedToken(sourcetoken=source_token, aligned=False)
        assert at.targettoken is None
        assert at.sourcetoken == source_token
        assert at.aligned is False

    def test_init_no_tokens(self) -> None:
        """Test initialization with no tokens."""
        at = AlignedToken()
        assert at.targettoken is None
        assert at.sourcetoken is None
        assert at.aligned is False


class TestAlignedTokenRepr:
    """Test AlignedToken.__repr__()."""

    def test_repr_with_target_aligned(self, target_token: Target) -> None:
        """Test repr with target token and aligned flag."""
        at = AlignedToken(targettoken=target_token, aligned=True)
        assert repr(at) == "<AlignedToken(targetid=41004003002, aligned)>"

    def test_repr_with_target_not_aligned(self, target_token: Target) -> None:
        """Test repr with target token but not aligned."""
        at = AlignedToken(targettoken=target_token, aligned=False)
        assert repr(at) == "<AlignedToken(targetid=41004003002)>"

    def test_repr_with_source_only(self, source_token: Source) -> None:
        """Test repr with source token only."""
        at = AlignedToken(sourcetoken=source_token)
        assert repr(at) == "<AlignedToken(sourceid=41004003001)>"

    def test_repr_no_tokens(self) -> None:
        """Test repr with no tokens."""
        at = AlignedToken()
        assert repr(at) == "<AlignedToken(no token)>"


class TestAlignedTokenComparison:
    """Test AlignedToken.__lt__() comparison method."""

    def test_compare_both_with_targets(
        self, source_token: Source, target_token: Target, target_token2: Target
    ) -> None:
        """Test comparison when both have target tokens."""
        at1 = AlignedToken(targettoken=target_token, sourcetoken=source_token)
        at2 = AlignedToken(targettoken=target_token2, sourcetoken=source_token)
        # Compare by target tokens
        assert at1 < at2
        assert not at2 < at1

    def test_compare_target_vs_source_both_have_source(
        self, source_token: Source, source_token2: Source, target_token: Target
    ) -> None:
        """Test comparison when one has target, other doesn't, but both have source."""
        at1 = AlignedToken(targettoken=target_token, sourcetoken=source_token)
        at2 = AlignedToken(sourcetoken=source_token2)
        # Compare by source tokens
        assert at1 < at2

    def test_compare_target_vs_source_self_no_source(
        self, source_token: Source, target_token: Target
    ) -> None:
        """Test comparison when self has target but no source, other has source."""
        at1 = AlignedToken(targettoken=target_token)  # 41004003002
        at2 = AlignedToken(sourcetoken=source_token)  # 41004003001
        # Compare target ID vs source ID (hack comparison)
        # "41004003002" < "41004003001" is False
        assert not at1 < at2

    def test_compare_source_vs_target_both_have_source(
        self, source_token: Source, source_token2: Source, target_token: Target
    ) -> None:
        """Test comparison when self has source only, other has target and source."""
        at1 = AlignedToken(sourcetoken=source_token)
        at2 = AlignedToken(targettoken=target_token, sourcetoken=source_token2)
        # Compare by source tokens
        assert at1 < at2

    def test_compare_source_vs_target_other_no_source(
        self, source_token: Source, target_token: Target
    ) -> None:
        """Test comparison when self has source, other has target but no source."""
        at1 = AlignedToken(sourcetoken=source_token)  # 41004003001
        at2 = AlignedToken(targettoken=target_token)  # 41004003002
        # Compare source ID vs target ID (hack comparison)
        # "41004003001" < "41004003002" is True
        assert at1 < at2

    def test_compare_self_has_target_other_has_neither_raises_error(
        self, target_token: Target
    ) -> None:
        """Test that comparison raises error when self has target, other has neither."""
        at1 = AlignedToken(targettoken=target_token)
        at2 = AlignedToken()
        with pytest.raises(ValueError, match="Cannot compare: other has neither target nor source"):
            at1 < at2

    def test_compare_self_has_neither_other_has_target_raises_error(
        self, target_token: Target
    ) -> None:
        """Test that comparison raises error when self has neither, other has target."""
        at1 = AlignedToken()
        at2 = AlignedToken(targettoken=target_token)
        with pytest.raises(ValueError, match="Cannot compare: self has neither target nor source"):
            at1 < at2


class TestAlignedTokenDisplay:
    """Test AlignedToken.display() method."""

    def test_display_both_tokens(
        self, source_token: Source, target_token: Target
    ) -> None:
        """Test display with both tokens."""
        at = AlignedToken(targettoken=target_token, sourcetoken=source_token)
        assert at.display() == " 41004003002 41004003001"

    def test_display_target_only(self, target_token: Target) -> None:
        """Test display with target token only."""
        at = AlignedToken(targettoken=target_token)
        assert at.display() == " 41004003002 -----------"

    def test_display_source_only(self, source_token: Source) -> None:
        """Test display with source token only."""
        at = AlignedToken(sourcetoken=source_token)
        assert at.display() == " ----------- 41004003001"

    def test_display_no_tokens(self) -> None:
        """Test display with no tokens."""
        at = AlignedToken()
        assert at.display() == " ----------- -----------"


class TestAlignedTokenIds:
    """Test AlignedToken.ids() method."""

    def test_ids_both_tokens(
        self, source_token: Source, target_token: Target
    ) -> None:
        """Test ids with both tokens."""
        at = AlignedToken(targettoken=target_token, sourcetoken=source_token)
        assert at.ids() == "41004003001 41004003002"

    def test_ids_source_only(self, source_token: Source) -> None:
        """Test ids with source token only."""
        at = AlignedToken(sourcetoken=source_token)
        assert at.ids() == "41004003001 -----------"

    def test_ids_target_only(self, target_token: Target) -> None:
        """Test ids with target token only."""
        at = AlignedToken(targettoken=target_token)
        assert at.ids() == "----------- 41004003002"

    def test_ids_no_tokens(self) -> None:
        """Test ids with no tokens."""
        at = AlignedToken()
        assert at.ids() == "----------- -----------"


class TestAlignedTokenAsdict:
    """Test AlignedToken.asdict() method."""

    def test_asdict_both_tokens(
        self, source_token: Source, target_token: Target
    ) -> None:
        """Test asdict with both source and target tokens."""
        at = AlignedToken(targettoken=target_token, sourcetoken=source_token)
        result = at.asdict()
        # Check target attributes
        assert result["targetid"] == "41004003002"
        assert result["targettext"] == "Listen"
        assert result["source_verse"] == "41004003"
        # Check source attributes
        assert result["sourceid"] == "41004003001"
        assert result["sourcetext"] == "ἀκούετε"
        assert result["strongs"] == "G0191"
        assert result["lemma"] == "ἀκούω"
        assert result["gloss"] == "hear"
        assert result["pos"] == "verb"
        # Check that 'id' and 'text' are not in the dict
        assert "id" not in result
        assert "text" not in result

    def test_asdict_target_only(self, target_token: Target) -> None:
        """Test asdict with target token only."""
        at = AlignedToken(targettoken=target_token)
        result = at.asdict()
        assert result["targetid"] == "41004003002"
        assert result["targettext"] == "Listen"
        assert result["source_verse"] == "41004003"
        # No source attributes
        assert "sourceid" not in result
        assert "sourcetext" not in result
        assert "strongs" not in result

    def test_asdict_source_only(self, source_token: Source) -> None:
        """Test asdict with source token only."""
        at = AlignedToken(sourcetoken=source_token)
        result = at.asdict()
        assert result["sourceid"] == "41004003001"
        assert result["sourcetext"] == "ἀκούετε"
        assert result["strongs"] == "G0191"
        assert result["lemma"] == "ἀκούω"
        # No target attributes
        assert "targetid" not in result
        assert "targettext" not in result
        assert "source_verse" not in result

    def test_asdict_no_tokens(self) -> None:
        """Test asdict with no tokens."""
        at = AlignedToken()
        result = at.asdict()
        assert result == {}
