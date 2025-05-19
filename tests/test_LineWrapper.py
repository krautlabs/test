import textwrap

import pytest
from pygments.token import Token

from pycheese.utils.linewrapper import *


def test_no_wrap_single_short_token():
    tokens = [
        ("import", "ff4689", "regular", Token.Keyword.Namespace, 6),
    ]
    expected = [tokens]
    result = wrap_tokens(tokens, width=10)
    assert result == expected


def test_wrap_single_long_token():
    tokens = [
        ("# a_longer_comment", "959077", "regular", Token.Comment.Single, 18),
    ]
    expected = [
        [
            ("# a_longer", "959077", "regular", Token.Comment.Single, 10),
            ("\n", "f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
        [
            ("_comment", "959077", "regular", Token.Comment.Single, 8),
        ],
    ]
    result = wrap_tokens(tokens, width=10)
    assert result == expected


def test_wrap_long_line_at_token():
    tokens = [
        ("class", "66d9ef", "regular", Token.Keyword, 5),
        (" ", "f8f8f2", "regular", Token.Text.Whitespace, 1),
        ("C", "a6e22e", "regular", Token.Name.Class, 1),
        (":", "f8f8f2", "regular", Token.Punctuation, 1),
    ]
    expected = [
        [
            ("class", "66d9ef", "regular", Token.Keyword, 5),
            # correct, spaces at start of new line are moved to end of previous
            (" ", "f8f8f2", "regular", Token.Text.Whitespace, 0),
            ("\n", "f8f8f2", "regular", Token.Text.Whitespace, 0),
        ],
        [
            ("", "f8f8f2", "regular", Token.Text.Whitespace, 1),
            ("C", "a6e22e", "regular", Token.Name.Class, 1),
            (":", "f8f8f2", "regular", Token.Punctuation, 1),
        ],
    ]

    result = wrap_tokens(tokens, width=5)
    assert result == expected


# def test_wrap_long_line_at_space_after_token():
#     tokens = [
#         ("class", "66d9ef", "regular", Token.Keyword, 5),
#         (" ", "f8f8f2", "regular", Token.Text.Whitespace, 1),
#         ("C", "a6e22e", "regular", Token.Name.Class, 1),
#         (":", "f8f8f2", "regular", Token.Punctuation, 1),
#     ]
#     expected = [
#         [
#             ("class", "66d9ef", "regular", Token.Keyword, 5),
#             (" ", "f8f8f2", "regular", Token.Text.Whitespace, 1),
#             ("", "a6e22e", "regular", Token.Name.Class, 0),
#             ("\n", "f8f8f2", "regular", Token.Text.Whitespace, 0),
#         ],
#         [
#             ("C", "a6e22e", "regular", Token.Name.Class, 1),
#             (":", "f8f8f2", "regular", Token.Punctuation, 1),
#         ],
#     ]
#     result = wrap_tokens(tokens, width=6)
#     assert result == expected


# def test_wrap_long_line_multiple_tokens():
#     code_tokens = [[("abc", "red", "bold"), ("defgh", "blue", "italic")]]
#     columns = 5
#     rows = 3
#     result = get_wrapped_lines(code_tokens[0], columns, rows)
#     expected = [
#         [("abc", "red", "bold"), ("de", "blue", "italic")],
#         [("fgh", "blue", "italic")],
#         [],
#     ]
#     assert result == expected
#


# def test_newline_splitting():
#     code_tokens = [
#         ("abc\n12345", "red", "bold"),
#     ]
#     columns = 10
#     rows = 3
#     result = get_wrapped_lines(code_tokens, columns, rows)
#     expected = [
#         [("abc", "red", "bold")],
#         [("12345", "red", "bold")],
#         [],
#     ]
#     assert result == expected
#

# def test_rows_limit_trimming():
#     code_tokens = [
#         ("abcdefghijklmnopqrstuvwxyz", "red", "bold"),
#     ]
#     columns = 5
#     rows = 3
#     result = get_wrapped_lines(code_tokens, columns, rows)
#     # Should keep last 3 wrapped lines only
#     expected = [
#         [("fghij", "red", "bold")],
#         [("klmno", "red", "bold")],
#         [("pqrst", "red", "bold")],
#     ]
#     assert result == expected


# def test_fill_empty_lines():
#     code_tokens = [("abc", "red", "bold")]
#     columns = 10
#     rows = 5
#     result = get_wrapped_lines(code_tokens, columns, rows)
#     assert len(result) == 5
#     assert result[0] == [("abc", "red", "bold")]
#     for line in result[1:]:
#         assert line == []
