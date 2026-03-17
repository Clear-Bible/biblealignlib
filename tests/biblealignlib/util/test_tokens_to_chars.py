"""Test tokens_to_chars."""

from biblealignlib.burrito import BaseToken
from biblealignlib.util.tokens_to_chars import tokens_to_chars


def make_token(id: str, text: str = "") -> BaseToken:
    """Return a BaseToken with the given id and text."""
    return BaseToken(id=id, text=text)


class TestTokensToChars:
    """Tests for tokens_to_chars."""

    def test_empty_sequences(self) -> None:
        """Two empty sequences produce empty char strings and a one-element array."""
        chars1, chars2, token_array = tokens_to_chars([], [])
        assert chars1 == ""
        assert chars2 == ""
        # index 0 is always unused placeholder
        assert token_array == [""]

    def test_single_token(self) -> None:
        """A single token encodes to a single character."""
        t = make_token("41004003001", "sower")
        chars1, chars2, token_array = tokens_to_chars([t], [])
        assert len(chars1) == 1
        assert chars2 == ""
        assert len(token_array) == 2  # placeholder + one token

    def test_same_token_reuses_encoding(self) -> None:
        """The same token id in both sequences maps to the same character."""
        t = make_token("41004003001", "sower")
        chars1, chars2, token_array = tokens_to_chars([t], [t])
        assert chars1 == chars2
        assert len(token_array) == 2  # only one unique token

    def test_different_tokens_get_different_chars(self) -> None:
        """Different token ids each get a distinct character."""
        t1 = make_token("41004003001", "a")
        t2 = make_token("41004003002", "b")
        chars1, chars2, token_array = tokens_to_chars([t1], [t2])
        assert chars1 != chars2
        assert len(token_array) == 3  # placeholder + two tokens

    def test_token_array_contains_tokens(self) -> None:
        """token_array entries at non-zero indices are BaseToken instances."""
        t1 = make_token("41004003001", "went")
        t2 = make_token("41004003002", "out")
        _, _, token_array = tokens_to_chars([t1, t2], [])
        assert token_array[1] is t1
        assert token_array[2] is t2

    def test_char_indices_match_token_array(self) -> None:
        """The ordinal of each encoded character indexes the correct token."""
        t1 = make_token("41004003001", "went")
        t2 = make_token("41004003002", "out")
        chars1, _, token_array = tokens_to_chars([t1, t2], [])
        for char, expected_token in zip(chars1, [t1, t2]):
            assert token_array[ord(char)] is expected_token

    def test_shared_tokens_across_sequences(self) -> None:
        """Tokens shared between sequences use the same encoding in both."""
        shared = make_token("41004003001", "the")
        only1 = make_token("41004003002", "sower")
        only2 = make_token("41004003003", "went")
        chars1, chars2, token_array = tokens_to_chars([shared, only1], [shared, only2])
        # first character of each sequence should be the same (shared token)
        assert chars1[0] == chars2[0]
        # second characters differ (distinct tokens)
        assert chars1[1] != chars2[1]
        assert len(token_array) == 4  # placeholder + 3 unique tokens

    def test_repeated_token_in_sequence(self) -> None:
        """A token that appears multiple times reuses the same character."""
        t = make_token("41004003001", "and")
        chars1, _, token_array = tokens_to_chars([t, t, t], [])
        assert len(chars1) == 3
        assert chars1[0] == chars1[1] == chars1[2]
        assert len(token_array) == 2  # only one unique token

    def test_encoding_starts_at_chr_1(self) -> None:
        """First unique token is encoded as chr(1) (index 0 is unused)."""
        t = make_token("41004003001", "x")
        chars1, _, _ = tokens_to_chars([t], [])
        assert ord(chars1[0]) == 1
