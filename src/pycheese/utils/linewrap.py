import argparse

from pygments.lexers import PythonLexer

from pycheese.utils.linewrap_core import tokenize, wrap_tokens


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Tokenize and wrap Python code.")
    parser.add_argument("filename", help="Path to the Python file to be tokenized.")
    parser.add_argument(
        "-c", "--columns", type=int, default=80, help="Width for wrapping lines."
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    with open(args.filename, "r", encoding="utf-8") as f:
        code = f.read()

    tokens = tokenize(code, PythonLexer(), "monokai")
    wrapped_tokens = wrap_tokens(tokens, width=args.columns)

    for row in wrapped_tokens:
        print("".join([str(token[0]) for token in row]), end="")


if __name__ == "__main__":
    main()
