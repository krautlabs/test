import textwrap

import pytest
from pygments.token import Token

from pycheese.utils.linewrap import *

newline_token = ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0)
single_token = ("import", "#ff4689", "regular", Token.Keyword.Namespace, 6)
four_tokens = [
    ("class", "#66d9ef", "regular", Token.Keyword, 5),
    (" ", "#f8f8f2", "regular", Token.Text.Whitespace, 1),
    ("C", "#a6e22e", "regular", Token.Name.Class, 1),
    (":", "#f8f8f2", "regular", Token.Punctuation, 1),
    ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
]


def test_tokenize():
    expected_monokai = [
        ("import", "#ff4689", "regular", Token.Keyword.Namespace, 6),
        (" ", "#f8f8f2", "regular", Token.Text.Whitespace, 1),
        ("os", "#f8f8f2", "regular", Token.Name.Namespace, 2),
        ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
    ]
    expected_bw = [
        ("import", "#000000", "bold", Token.Keyword.Namespace, 6),
        (" ", "#000000", "regular", Token.Text.Whitespace, 1),
        ("os", "#000000", "bold", Token.Name.Namespace, 2),
        ("\n", "#000000", "regular", Token.Text.Whitespace, 0),
    ]
    code = """import os"""
    result_monokai = tokenize(code, PythonLexer(), "monokai")
    result_bw = tokenize(code, PythonLexer(), "bw")
    assert result_bw == expected_bw
    assert result_monokai == expected_monokai


@pytest.mark.parametrize("pos", [-1])
def test_split_negative(pos):
    with pytest.raises(ValueError):
        split_token(single_token, pos=pos)


@pytest.mark.parametrize("pos", [len(single_token[0])])
def test_split_after_token(pos):
    """split at len(token) + 1"""
    with pytest.raises(ValueError):
        split_token(single_token, pos=pos)


@pytest.mark.parametrize("pos", [0])
def test_split_zero(pos):
    expected = [newline_token, single_token]
    result = split_token(single_token, pos=pos)
    assert result == expected


@pytest.mark.parametrize("pos", [1])
def test_split_one(pos):
    expected = [
        ("i", "#ff4689", "regular", Token.Keyword.Namespace, 1),
        newline_token,
        ("mport", "#ff4689", "regular", Token.Keyword.Namespace, 5),
    ]
    result = split_token(single_token, pos=pos)
    assert result == expected


def test_no_wrap_single_short_token():
    expected = [[single_token]]
    result = wrap_tokens([single_token], width=10)
    assert result == expected


def test_wrap_single_long_token():
    tokens = [
        ("# a_longer_comment", "#959077", "regular", Token.Comment.Single, 18),
    ]
    expected = [
        [
            ("# a_longer", "#959077", "regular", Token.Comment.Single, 10),
            ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
        [
            ("_comment", "#959077", "regular", Token.Comment.Single, 8),
        ],
    ]
    result = wrap_tokens(tokens, width=10)
    assert result == expected


def test_wrap_long_line_at_last_character_of_token():
    expected = [
        [
            ("class", "#66d9ef", "regular", Token.Keyword, 5),
            ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
        [
            ("C", "#a6e22e", "regular", Token.Name.Class, 1),
            (":", "#f8f8f2", "regular", Token.Punctuation, 1),
            ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
    ]
    result = wrap_tokens(four_tokens, width=5)
    assert result == expected


def test_wrap_long_line_at_space_after_token():
    expected = [
        [
            ("class", "#66d9ef", "regular", Token.Keyword, 5),
            (" ", "#f8f8f2", "regular", Token.Text.Whitespace, 1),
            ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
        [
            ("C", "#a6e22e", "regular", Token.Name.Class, 1),
            (":", "#f8f8f2", "regular", Token.Punctuation, 1),
            ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
    ]
    result = wrap_tokens(four_tokens, width=6)
    assert result == expected


def test_wrap_long_line_at_existing_newline():
    expected = [
        [
            ("class", "#66d9ef", "regular", Token.Keyword, 5),
            (" ", "#f8f8f2", "regular", Token.Text.Whitespace, 1),
            ("C", "#a6e22e", "regular", Token.Name.Class, 1),
            (":", "#f8f8f2", "regular", Token.Punctuation, 1),
            ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
    ]
    result = wrap_tokens(four_tokens, width=9)
    assert result == expected
