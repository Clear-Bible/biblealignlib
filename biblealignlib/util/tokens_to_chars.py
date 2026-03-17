"""Convert two sequences of tokens to sequences of Unicode characters, and a list of the unique tokens.

You might want to do this if you want to use the diff_match_patch
library, which works on characters.

"""

from typing import Callable

from biblealignlib.burrito import BaseToken


def tokens_to_chars(
    seq1: list[BaseToken],
    seq2: list[BaseToken],
    idfun: Callable = lambda token: token.id + token.text,
) -> tuple[str, str, list[str]]:
    """Encode each unique token as a single Unicode character.

    Default identity function for tokens is id + text. This is the same
    idea as diff-match-patch's line-mode compression, but adapted to
    tokens.

    """
    token_array = [""]  # token_array[0] unused
    token_hash = {}

    def encode(seq: list[BaseToken]) -> str:
        chars = []
        for token in seq:
            tid = idfun(token)
            if tid not in token_hash:
                token_hash[tid] = len(token_array)
                token_array.append(token)
            chars.append(chr(token_hash[tid]))
        return "".join(chars)

    return encode(seq1), encode(seq2), token_array
