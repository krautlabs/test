import argparse
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name


# Custom formatter to extract tokens with styles
class TokenFormatter(Formatter):
    def __init__(self, **options):
        super().__init__(**options)
        self.styles = {}
        self.result = []
        style = get_style_by_name(options.get("style", "monokai"))
        for token, style_def in style:
            if style_def["color"]:
                self.styles[token] = "#" + style_def["color"]
            else:
                self.styles[token] = "#ffffff"

    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            color = self.styles.get(ttype, "#ffffff")
            self.result.append((value, color))


def get_wrapped_lines(code_tokens, columns, rows):
    # Process tokens into lines (now with wrapping based on column limit)
    raw_lines = []
    current_line = []
    current_line_text = ""

    for token, color in code_tokens:
        parts = token.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                raw_lines.append((current_line, current_line_text))
                current_line = []
                current_line_text = ""
            current_line.append((part, color))
            current_line_text += part

    if current_line:
        raw_lines.append((current_line, current_line_text))

    # Apply column wrapping
    wrapped_lines = []
    for tokens, full_text in raw_lines:
        if len(full_text) <= columns:
            wrapped_lines.append(tokens)
        else:
            # Wrap this line into multiple lines
            wrapped_text_lines = textwrap.wrap(
                full_text, width=columns, replace_whitespace=False
            )

            # Need to split the tokens according to the wrapping
            for wrapped_line in wrapped_text_lines:
                new_tokens = []
                remaining_text = wrapped_line

                for token, color in tokens:
                    if not remaining_text:
                        break

                    if token in remaining_text:
                        # Find position where token occurs in remaining text
                        pos = remaining_text.find(token)
                        if pos == 0:
                            # Token is at the beginning of the remaining text
                            use_len = min(len(token), len(remaining_text))
                            new_tokens.append((token[:use_len], color))
                            remaining_text = remaining_text[use_len:]
                        else:
                            # Skip characters before the token
                            remaining_text = remaining_text[pos:]
                            use_len = min(len(token), len(remaining_text))
                            new_tokens.append((token[:use_len], color))
                            remaining_text = remaining_text[use_len:]
                    else:
                        # Token might be partially in this line
                        common_prefix_len = 0
                        for i in range(min(len(token), len(remaining_text))):
                            if token[i] != remaining_text[i]:
                                break
                            common_prefix_len = i + 1

                        if common_prefix_len > 0:
                            new_tokens.append((token[:common_prefix_len], color))
                            remaining_text = remaining_text[common_prefix_len:]

                wrapped_lines.append(new_tokens)

    # Limit to specified number of rows (keep last 'rows' if overflow)
    if len(wrapped_lines) > rows:
        wrapped_lines = wrapped_lines[-rows:]

    # Ensure we have exactly 'rows' number of lines
    while len(wrapped_lines) < rows:
        wrapped_lines.append([])  # Add empty lines to fill the terminal

    return wrapped_lines


def render_terminal_image(
    wrapped_lines,
    font_path,
    font_size=20,
    padding=20,
    margin=20,
    line_spacing=1.4,
    theme="monokai",
    output="rendered_terminal.png",
    rows=24,
    columns=80,
    corner_radius=16,
):
    font = ImageFont.truetype(font_path, font_size)
    line_height = int(font_size * line_spacing)
    char_width = font.getlength("M")

    window_width = int(columns * char_width + 2 * padding)
    window_height = int(rows * line_height + 2 * padding + 30)
    img_width = int(window_width + 2 * margin)
    img_height = int(window_height + 2 * margin)

    # Create shadow background with transparency
    shadow_offset = 10
    shadow_blur = 6
    assert shadow_offset <= margin, f"{shadow_offset=}, {margin=}."

    base = Image.new(
        "RGBA",
        (img_width, img_height),
        (255, 255, 255, 0),
    )
    shadow = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [
            margin + shadow_offset,
            margin + shadow_offset,
            window_width + shadow_offset,
            window_height + shadow_offset,
        ],
        radius=corner_radius,
        fill=(0, 0, 0, 180),
    )
    base.paste(shadow, (margin, margin), shadow)
    base = base.filter(ImageFilter.GaussianBlur(shadow_blur))

    # Create rounded terminal window
    img = Image.new("RGBA", (window_width, window_height), (0, 0, 0, 0))
    mask = Image.new("L", (window_width, window_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [0, 0, window_width, window_height], radius=corner_radius, fill=255
    )

    terminal = Image.new("RGBA", (window_width, window_height), (40, 42, 54))
    terminal_draw = ImageDraw.Draw(terminal)

    # Draw top bar with traffic lights
    bar_height = 30
    terminal_draw.rectangle([(0, 0), (window_width, bar_height)], fill=(30, 30, 30))
    traffic_colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
    for i, color in enumerate(traffic_colors):
        terminal_draw.ellipse(
            [(padding + i * 20, 8), (padding + i * 20 + 12, 20)], fill=color
        )

    # Draw code
    y = padding + bar_height
    for line in wrapped_lines:
        x = padding
        for token, color in line:
            terminal_draw.text((x, y), token, font=font, fill=color)
            x += font.getlength(token)
        y += line_height

    # Apply rounded corners mask
    img.paste(terminal, (0, 0), mask)

    # Paste onto shadow base
    base.paste(img, (margin, margin), img)
    base = base.filter(ImageFilter.GaussianBlur(0.5))
    base.convert("RGB").save(output, "PNG")


def main():
    parser = argparse.ArgumentParser(
        description="Render Python code into a styled terminal PNG."
    )
    parser.add_argument("source_file", type=str, help="Path to the .py source file")
    parser.add_argument(
        "--theme", type=str, default="monokai", help="Syntax highlighting theme"
    )
    parser.add_argument(
        "--font",
        type=str,
        default="FiraCode-Regular.ttf",
        help="Path to the font file (TTF)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="rendered_terminal.png",
        help="Output PNG file path",
    )
    parser.add_argument(
        "--rows", type=int, default=24, help="Number of rows in the terminal"
    )
    parser.add_argument(
        "--columns", type=int, default=80, help="Number of columns in the terminal"
    )
    args = parser.parse_args()

    if not Path(args.source_file).exists() or not args.source_file.endswith(".py"):
        raise FileNotFoundError("The source file must exist and be a .py file.")

    if not Path(args.font).exists():
        raise FileNotFoundError("Font file not found. Provide a valid TTF file.")

    with open(args.source_file, "r", encoding="utf-8") as f:
        code = f.read()

    formatter = TokenFormatter(style=args.theme)
    highlight(code, PythonLexer(), formatter)

    wrapped_lines = get_wrapped_lines(
        formatter.result,
        args.columns,
        args.rows,
    )

    render_terminal_image(
        wrapped_lines,
        args.font,
        theme=args.theme,
        output=args.output,
        rows=args.rows,
        columns=args.columns,
        corner_radius=16,
    )


if __name__ == "__main__":
    main()
