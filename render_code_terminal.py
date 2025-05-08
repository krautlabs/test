import argparse
import os
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


def render_terminal_image(
    code_tokens,
    font_path,
    font_size=20,
    padding=20,
    line_spacing=1.4,
    theme="monokai",
    output="rendered_terminal.png",
):
    font = ImageFont.truetype(font_path, font_size)
    line_height = int(font_size * line_spacing)
    lines = []
    current_line = []
    for token, color in code_tokens:
        parts = token.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                lines.append(current_line)
                current_line = []
            current_line.append((part, color))
    if current_line:
        lines.append(current_line)

    max_line_width = max(
        sum(font.getlength(token) for token, _ in line) for line in lines
    )
    img_width = int(max_line_width + 2 * padding)
    img_height = int(len(lines) * line_height + 2 * padding + 30)

    corner_radius = 16

    # Create shadow background with transparency
    base = Image.new("RGBA", (img_width + 20, img_height + 20), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    base.paste(shadow, (10, 10), shadow)

    # Create rounded terminal window
    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    mask = Image.new("L", (img_width, img_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [0, 0, img_width, img_height], radius=corner_radius, fill=255
    )

    terminal = Image.new("RGBA", (img_width, img_height), (40, 42, 54))
    terminal_draw = ImageDraw.Draw(terminal)

    # Draw top bar with traffic lights
    bar_height = 30
    terminal_draw.rectangle([(0, 0), (img_width, bar_height)], fill=(30, 30, 30))
    traffic_colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
    for i, color in enumerate(traffic_colors):
        terminal_draw.ellipse(
            [(padding + i * 20, 8), (padding + i * 20 + 12, 20)], fill=color
        )

    # Draw code
    y = padding + bar_height
    for line in lines:
        x = padding
        for token, color in line:
            terminal_draw.text((x, y), token, font=font, fill=color)
            x += font.getlength(token)
        y += line_height

    # Apply rounded corners mask
    img.paste(terminal, (0, 0), mask)

    # Paste onto shadow base
    base.paste(img, (0, 0), img)
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
    args = parser.parse_args()

    if not Path(args.source_file).exists() or not args.source_file.endswith(".py"):
        raise FileNotFoundError("The source file must exist and be a .py file.")

    if not Path(args.font).exists():
        raise FileNotFoundError("Font file not found. Provide a valid TTF file.")

    with open(args.source_file, "r", encoding="utf-8") as f:
        code = f.read()

    formatter = TokenFormatter(style=args.theme)
    highlight(code, PythonLexer(), formatter)
    render_terminal_image(
        formatter.result, args.font, theme=args.theme, output=args.output
    )


if __name__ == "__main__":
    main()
