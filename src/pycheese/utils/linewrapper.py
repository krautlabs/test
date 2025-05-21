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


def split_token(token, pos):
    """Split a single token and insert a newline token at `pos`.

    Splitting at pos=0 will emit two tokens: a newline token and the original
    token. Splitting at the last index (e.g. pos=3 for 'def') will emit a token
    that has all but the last character, followed by a newline token, followed
    by a token containing the last character of the original token. Tokens
    cannot be split past their last index. I.e. this function will never emit
    the original token followed by a newline token.

    Spaces that end up at the beginning of the new line (i.e. beginning of last
    token) will be moved to the end of the first token. This might create a
    token that exceeds the specified length. At this point users would need to
    strip spaces manually at line ends if that behaviour is not desired.
    """
    max_pos = max(0, token[4] - 1)
    if pos < 0 or max_pos < pos:
        raise ValueError(f"Cannot split {token=} at {pos=}, use [0..{max_pos}]")

    # don't split tokens with 0 printable length
    if token[4] == 0:
        return [token]

    newline_token = ("\n", "f8f8f2", "regular", Token.Text.Whitespace, 0)

    head_value = token[0][:pos]
    tail_value = token[0][pos:]
    head_printable_len = len(head_value.rstrip("\r\n"))
    tail_printable_len = len(tail_value.rstrip("\r\n"))

    # add leading spaces of tail token to end of head token
    match = re.match(r"\s+", tail_value)
    leading_spaces = match.group() if match else ""
    if leading_spaces:
        head_value += leading_spaces
        tail_value = tail_value[len(leading_spaces) :]

    out_tokens = [
        (head_value, *token[1:4], head_printable_len),
        newline_token,
        (tail_value, *token[1:4], tail_printable_len),
    ]
    # remove tokens with empty values
    return [t for t in out_tokens if t[0]]


def wrap_tokens(tokens, width=80):
    tokens.reverse()
    single_row = []
    rows = []
    char_count = 0

    while tokens:
        token = tokens.pop()

        if char_count + token[4] > width:
            pos = width - char_count

            print(f"splitting {pos=}, {char_count=}, {token[0]=}")
            input(">>> press to continue")

            head, *tail = split_token(token, pos)

            # doesn't advance if head is newline that doesn't increase char_count
            # either repreat newline finish row logic from below

            print(f"got {head} & {tail}")

            single_row.append(head)
            tokens.extend(tail[::-1])
            char_count += head[4]
            print(f"append split head ({char_count}) {repr(head[0])}")
            continue

        single_row.append(token)
        char_count += token[4]
        print(f"append token ({char_count}) {repr(token[0])}")

        if token[0] == "\n":
            rows.append(single_row)
            print("append row", [t[0] for t in single_row])
            single_row = []
            char_count = 0

    if single_row:
        rows.append(single_row)

    return rows


def ruler(n=80):
    output = [f"{(i%16):x}" for i in range(n)]
    return "".join(output)


def main():
    code1 = textwrap.dedent(
        """\
        def example_very_long_function():
            print("This is   a very long line that should be wrapped if it exceeds the terminal width.")
            return True
    """
    )
    code2 = "class C:"
    code2 = "if a > b:"

    # print(
    #     split_token(
    #         ("text", "959077", "regular", Token.Comment.Single, 18),
    #         pos=0,
    #     )
    # )
    tokens = [
        ("class", "66d9ef", "regular", Token.Keyword, 5),
        (" ", "f8f8f2", "regular", Token.Text.Whitespace, 1),
        ("C", "a6e22e", "regular", Token.Name.Class, 1),
        (":", "f8f8f2", "regular", Token.Punctuation, 1),
    ]

    # tokens = tokenize(code1, lexer=PythonLexer(ensurenl=False), style="monokai")
    # print("tokens = ", [t[0] for t in tokens])
    wt = wrap_tokens(tokens, width=6)
    print("_", ruler(18))
    for i, l in enumerate(wt):
        # print(i, [repr(t[0]) for t in l])
        print(i, "".join([str(t[0]).replace(" ", "_") for t in l]), end="")
    # for l in wt:
    #     print("|".join([t[0] for t in l]), end="")

    # print(tokens[0])
    # print(split_token(tokens[0], pos=2))

    # print()
    # single_token = ("import", "ff4689", "regular", Token.Keyword.Namespace, 6)
    # print(split_token(single_token, 0))
    # print(wrap_tokens([single_token], width=10))


if __name__ == "__main__":
    main()
