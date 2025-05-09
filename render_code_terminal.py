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


class Renderer:
    def __init__(
        self,
        font_path,
        font_size=20,
        padding=20,
        margin=20,
        line_spacing=1.4,
        rows=24,
        columns=80,
        corner_radius=16,
    ):
        self.font_path = font_path
        self.font_size = font_size
        self.padding = padding
        self.margin = margin
        self.line_spacing = line_spacing
        self.rows = rows
        self.columns = columns
        self.corner_radius = corner_radius

        self.window_image = None
        self.font = None
        self.line_height = None
        self.mask = None
        self.img = None
        self.base = None
        self.bar_height = 30

        self._init_font_properties()
        self._init_image_properties()

    def _init_font_properties(self):
        self.font = ImageFont.truetype(self.font_path, self.font_size)
        self.line_height = int(self.font_size * self.line_spacing)
        self.char_width = self.font.getlength("M")

    def _init_image_properties(self):
        self.window_width = int(self.columns * self.char_width + 2 * self.padding)
        self.window_height = int(self.rows * self.line_height + 2 * self.padding + 30)
        self.img_width = int(self.window_width + 2 * self.margin)
        self.img_height = int(self.window_height + 2 * self.margin)

    def render_terminal_window(self, shadow_offset=10, shadow_blur=6):
        """Render a stylized terminal window background resembling macOS.

        This method creates an image of a terminal window with a drop shadow which
        can be customized by adjusting its offset and blur. The image is cached and
        can be re-used as background for different code snippets.

        Parameters:
            shadow_offset (int): The distance in pixels that the shadow is offset
                from the terminal window. Defaults to 10.
            shadow_blur (int): The level of blur applied to the shadow. Higher
                values result in a softer shadow. Defaults to 6.
        """
        assert shadow_offset <= self.margin, f"{shadow_offset=}, {self.margin=}."

        # create background
        self.base = Image.new(
            "RGBA", (self.img_width, self.img_height), (255, 255, 255, 0)
        )
        self.base = create_purple_gradient(self.img_width, self.img_height)

        # create shadow
        shadow = Image.new(
            "RGBA", (self.img_width, self.img_height), (255, 255, 255, 0)
        )
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [
                self.margin + shadow_offset,
                self.margin + shadow_offset,
                self.window_width + shadow_offset,
                self.window_height + shadow_offset,
            ],
            radius=self.corner_radius,
            fill=(0, 0, 0, 180),
        )
        self.base.paste(shadow, (self.margin, self.margin), shadow)
        self.base = self.base.filter(ImageFilter.GaussianBlur(shadow_blur))

        # Create rounded terminal window
        self.img = Image.new(
            "RGBA", (self.window_width, self.window_height), (0, 0, 0, 0)
        )
        self.mask = Image.new("L", (self.window_width, self.window_height), 0)
        mask_draw = ImageDraw.Draw(self.mask)
        mask_draw.rounded_rectangle(
            [0, 0, self.window_width, self.window_height],
            radius=self.corner_radius,
            fill=255,
        )

        terminal = Image.new(
            "RGBA", (self.window_width, self.window_height), (40, 42, 54)
        )
        terminal_draw = ImageDraw.Draw(terminal)

        # Draw top bar with traffic lights
        self.bar_height = 30
        terminal_draw.rectangle(
            [(0, 0), (self.window_width, self.bar_height)], fill=(30, 30, 30)
        )
        traffic_colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
        for i, color in enumerate(traffic_colors):
            terminal_draw.ellipse(
                [(self.padding + i * 20, 8), (self.padding + i * 20 + 12, 20)],
                fill=color,
            )

        self.window_image = terminal

    def render_text_to_window(self, code, style="monokai"):
        assert self.window_image, "create window image before rendering text"

        formatter = TokenFormatter(style=style)
        highlight(code, PythonLexer(), formatter)

        wrapped_lines = get_wrapped_lines(
            formatter.result,
            self.columns,
            self.rows,
        )

        terminal_draw = ImageDraw.Draw(self.window_image)
        y = self.padding + self.bar_height
        for line in wrapped_lines:
            x = self.padding
            for token, color in line:
                terminal_draw.text((x, y), token, font=self.font, fill=color)
                x += self.font.getlength(token)
            y += self.line_height

        # Apply rounded corners mask
        self.img.paste(self.window_image, (0, 0), self.mask)

        # Paste onto shadow base
        self.base.paste(self.img, (self.margin, self.margin), self.img)
        self.base = self.base.filter(ImageFilter.GaussianBlur(0.5))

    def save_image(self, filename="rendered_code.png"):
        self.base.convert("RGB").save(filename, "PNG")
        print(f'Image saved to "{filename}".')


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

    renderer = Renderer(
        font_path=args.font,
        rows=args.rows,
        columns=args.columns,
        corner_radius=16,
        font_size=20,
    )
    renderer.render_terminal_window(shadow_offset=10, shadow_blur=0)
    renderer.render_text_to_window(code, style=args.theme)
    renderer.save_image(args.output)


def create_purple_gradient(width, height, start_color=None, end_color=None):
    import math

    # Monokai-style purple gradient (dark to light purple)
    start_color = (93, 80, 124)
    end_color = (151, 125, 201)

    image = Image.new("RGB", (width, height))
    angle_rad = math.radians(-120)

    # Gradient vector components
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)

    for y in range(height):
        for x in range(width):
            # Project point (x, y) onto gradient direction vector
            projection = x * dx + y * dy
            # Normalize projection to range 0–1
            normalized = (projection - min(0, dx * width + dy * height)) / (
                abs(dx) * width + abs(dy) * height
            )
            normalized = max(0, min(1, normalized))  # Clamp to [0, 1]

            # Interpolate colors
            r = int(start_color[0] * (1 - normalized) + end_color[0] * normalized)
            g = int(start_color[1] * (1 - normalized) + end_color[1] * normalized)
            b = int(start_color[2] * (1 - normalized) + end_color[2] * normalized)

            image.putpixel((x, y), (r, g, b))

    return image


if __name__ == "__main__":
    main()
