import argparse
import re
import textwrap

from pygments import lex
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name
from pygments.token import Token


def get_token_text_style(style_def):
    """Get token style as string from list of booleans.

    For example {"bold": True, "italic": True} returns "bold_italic".
    """
    style_map = {
        (False, False): "regular",
        (False, True): "italic",
        (True, False): "bold",
        (True, True): "bold_italic",
    }
    return style_map[(style_def["bold"], style_def["italic"])]


def tokenize(code, lexer, style="default", default_text_color="#000000"):
    """Translates code into tokens with type setting attributes.

    # Token consist of the token value, color, text style, token type and
    # printable length. The length excludes non-printable characters like '\n'.

    Example:
        ('def', '#66d9ef', 'regular', Token.Keyword, 3)
    """
    tokens = list(lex(code, lexer))

    style = get_style_by_name(style)
    style_dict = dict(style)

    l = []
    for tok_type, tok_val in tokens:
        # Get style attributes (color, bold, italic, etc.)
        style_attrs = style_dict.get(tok_type) or style_dict.get(tok_type.parent) or ()
        if style_attrs["color"] is None:
            color = default_text_color
        else:
            color = "#" + style_attrs["color"]  # test if valid color
        l.append(
            (
                tok_val,
                color,
                get_token_text_style(style_attrs),
                tok_type,
                len(tok_val.rstrip("\r\n")),
            )
        )
    return l


def split_token(token, pos):
    """Split a single token and insert a newline token at `pos`.

    Splitting at pos=0 will emit two tokens: a newline token and the original
    token. Splitting at the last index (e.g. pos=3 for 'def') will emit a token
    that has all but the last character, followed by a newline token, followed
    by a token containing the last character of the original token. Tokens
    cannot be split past their last index. I.e. this function will never emit
    the original token followed by a newline token.

    Spaces that end up at the beginning of the new line (i.e. beginning of last
    token) will be removed.
    """
    max_pos = max(0, token[4] - 1)
    if pos < 0 or max_pos < pos:
        raise ValueError(f"Cannot split {token=} at {pos=}, use [0..{max_pos}]")

    # don't split tokens with 0 printable length
    if token[4] == 0:
        return [token]

    newline_token = ("\n", "#f8f8f2", "regular", Token.Text.Whitespace, 0)

    head_value = token[0][:pos]
    tail_value = token[0][pos:]
    head_printable_len = len(head_value.rstrip("\r\n"))
    tail_printable_len = len(tail_value.rstrip("\r\n"))

    # remove leading spaces from tail token
    match = re.match(r"\s+", tail_value)
    leading_spaces = match.group() if match else ""
    if leading_spaces:
        tail_value = tail_value[len(leading_spaces) :]
        tail_printable_len -= len(leading_spaces)

    out_tokens = [
        (head_value, *token[1:4], head_printable_len),
        newline_token,
        (tail_value, *token[1:4], tail_printable_len),
    ]
    # only return tokens with non-empty values
    return [t for t in out_tokens if t[0]]


def wrap_tokens(tokens, width=80):
    token_stack = tokens[::-1]
    single_row = []
    rows = []
    char_count = 0

    while token_stack:
        token = token_stack.pop()

        if char_count + token[4] > width:
            pos = width - char_count
            token, *tail = split_token(token, pos)
            token_stack.extend(tail[::-1])

        single_row.append(token)
        char_count += token[4]

        if token[0] == "\n":
            rows.append(single_row)
            single_row = []
            char_count = 0

    if single_row:
        rows.append(single_row)

    return rows


def ruler(n=80):
    output = [f"{(i%16):x}" for i in range(n)]
    return "".join(output)


def main():
    parser = argparse.ArgumentParser(description="Tokenize and wrap Python code.")
    parser.add_argument("filename", help="Path to the Python file to be tokenized.")
    parser.add_argument(
        "-c", "--columns", type=int, default=80, help="Width for wrapping lines."
    )
    args = parser.parse_args()

    with open(args.filename, "r", encoding="utf-8") as f:
        code = f.read()

    tokens = tokenize(code, PythonLexer(), "monokai")
    wrapped_tokens = wrap_tokens(tokens, width=args.columns)

    for row in wrapped_tokens:
        print("".join([str(token[0]) for token in row]), end="")


if __name__ == "__main__":
    main()
