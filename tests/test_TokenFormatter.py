import pytest
from pygments.token import Token

from pycheese import TokenFormatter


@pytest.mark.parametrize(
    "theme, token_data, expected",
    [
        ("monokai", (Token.Keyword, "def"), ("def", "#66d9ef", "regular")),
        ("monokai", (Token.Text, "    "), ("    ", "#f8f8f2", "regular")),
        ("monokai", (Token.Name, "var1"), ("var1", "#f8f8f2", "regular")),
        ("bw", (Token.Keyword, "import"), ("import", "#000000", "bold")),
    ],
)
def test_tokenformatter_basic_formatting(theme, token_data, expected):
    formatter = TokenFormatter(default_text_color="#000000", style=theme)
    formatter.format([token_data], outfile=None)

    assert formatter.result[0] == expected
