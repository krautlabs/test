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


def tokenize(code, lexer, style="default"):
    """Translates code into tokens with type setting attributes.

    # Token consist of the token value, color, text style, token type and
    # printable length. The length excludes non-printable characters like '\n'.

    Example:
        ('def', '66d9ef', 'regular', Token.Keyword, 3)
    """
    tokens = list(lex(code, lexer))

    style = get_style_by_name(style)
    style_dict = dict(style)

    l = []
    for tok_type, tok_val in tokens:
        # Get style attributes (color, bold, italic, etc.)
        style_attrs = style_dict.get(tok_type) or style_dict.get(tok_type.parent) or ()
        l.append(
            (
                tok_val,
                style_attrs["color"],
                get_token_text_style(style_attrs),
                tok_type,
                len(tok_val.rstrip("\r\n")),
            )
        )
    return l


# def wrap_code_lines(code: str, width: int) -> list[str]:
#     wrapped_lines = []
#     for line in code.splitlines():
#         wrapped = textwrap.wrap(
#             line,
#             width=width,
#             expand_tabs=False,
#             replace_whitespace=False,
#             drop_whitespace=False,
#         )
#         if not wrapped:
#             wrapped_lines.extend(["", "\n"])
#             continue
#
#         # Move any leading whitespace from segment to end of previous line
#         adjusted = [wrapped[0]]
#         for segment in wrapped[1:]:
#             leading_spaces = re.match(r"\s*", segment).group()
#             adjusted[-1] += leading_spaces
#             adjusted.append(segment[len(leading_spaces) :])
#
#         for part in adjusted:
#             wrapped_lines.append(part)
#             wrapped_lines.append("\n")
#     return wrapped_lines


def split_token(token, pos):
    head_value = token[0][:pos]
    tail_value = token[0][pos:]
    head_printable_len = len(head_value.rstrip("\r\n"))
    tail_printable_len = len(tail_value.rstrip("\r\n"))
    newline_token = ("\n", "f8f8f2", "regular", Token.Text.Whitespace, 0)

    match = re.match(r"\s+", tail_value)
    leading_spaces = match.group() if match else ""
    if leading_spaces and True:
        head_value += leading_spaces
        tail_value = tail_value[len(leading_spaces) :]

    return [
        (head_value, *token[1:4], head_printable_len),
        newline_token,
        (tail_value, *token[1:4], tail_printable_len),
    ]


def wrap_tokens(tokens, width=80):
    wrapped_tokens = []
    wrapped_lines = []
    nchars = 0

    for token in tokens:
        tail = token
        nchars += tail[4]

        while nchars > width:
            pos = tail[4] - nchars + width
            head, newline, tail = split_token(tail, pos)
            # print(
            #     f"{nchars:02d}: splitting ({pos}) {head[0]!r}, {newline[0]!r}, {tail[0]!r}"
            # )
            wrapped_lines.append(wrapped_tokens + [head, newline])
            wrapped_tokens = []
            nchars = tail[4]

        if tail[0] == "\n":
            wrapped_lines.append(wrapped_tokens + [tail])
            wrapped_tokens = []
            nchars = 0
            # print(f"{nchars:02d}: newline {tail}")
        else:
            wrapped_tokens.extend([tail])
            # print(f"{nchars:02d}: appending {tail}")

    if wrapped_tokens:
        wrapped_lines.append(wrapped_tokens)

    return wrapped_lines


def ruler(n=80):
    output = [f"{(i%16):x}" for i in range(n)]
    return "".join(output)


def main():
    code = textwrap.dedent(
        """\
        def example_very_long_function():
            print("This is   a very long line that should be wrapped if it exceeds the terminal width.")
            return True
    """
    )
    code = "class C:"

    tokens = tokenize(code, lexer=PythonLexer(ensurenl=False), style="monokai")
    print("tokens = ", tokens)
    wt = wrap_tokens(tokens, width=6)
    print("expected =", wt)
    # for l in wt:
    #     print("|".join([t[0] for t in l]), end="")


if __name__ == "__main__":
    main()
