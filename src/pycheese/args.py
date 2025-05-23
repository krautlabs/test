import argparse


def get_argparser():
    parser = argparse.ArgumentParser(
        description="Render Python code into a styled terminal PNG."
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to the .py source file",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="monokai",
        help="Syntax highlighting style",
    )
    parser.add_argument(
        "--font",
        type=str,
        default="JetBrainsMono",
        # help="Path to the font file (TTF)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="rendered_terminal.png",
        help="Output PNG file path",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=24,
        help="Number of rows in the terminal",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=80,
        help="Number of columns in the terminal",
    )
    return parser
