import argparse
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont
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

        self.window_layer = None
        self.font = None
        self.line_height = None
        self.mask = None
        self.img = None
        self.bg_layer = None
        self.bar_height = 30
        self.shadow_layer = None
        self.final_image = None

        self.shadow_offset = 10
        self.shadow_blur = 6
        self.shadow_color = "black"
        self.shadow_alpha = 180

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

    def render_background_layer(self, first_color="white", second_color=None):
        """Render solid or gradient background layer."""
        rgba1 = any_color_to_rgba(first_color)

        if second_color is None:
            self.bg_layer = create_uniform_background(
                self.img_width,
                self.img_height,
                color=first_color,
            )
        else:
            self.bg_layer = create_gradient_background(
                self.img_width,
                self.img_height,
                start_color=first_color,
                end_color=second_color,
            )

    def render_shadow_layer(
        self,
        shadow_offset=10,
        shadow_blur=6,
        shadow_color="black",
        shadow_alpha=180,
        corner_radius=6,
    ):
        """Render floating window shadow layer."""
        rgba = any_color_to_rgba(shadow_color)
        assert 0 <= shadow_alpha <= 255, f"{shadow_alpha=} is outside range [0..255]"
        rgba = rgba[:3] + (shadow_alpha,)
        shadow = Image.new("RGBA", (self.img_width, self.img_height), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [
                self.margin + shadow_offset,
                self.margin + shadow_offset,
                self.margin + self.window_width + shadow_offset,
                self.margin + self.window_height + shadow_offset,
            ],
            radius=corner_radius,
            fill=(rgba),
        )
        self.shadow_layer = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))

    def create_window_mask(self):
        # create mask to round edges of terminal window
        self.mask2 = Image.new("L", (self.window_width, self.window_height), 0)
        mask_draw = ImageDraw.Draw(self.mask2)
        mask_draw.rounded_rectangle(
            [0, 0, self.window_width, self.window_height],
            radius=self.corner_radius,
            fill=255,
        )

    def render_window_layer(self):
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
        # assert (
        #     self.shadow_offset <= self.margin
        # ), f"{self.shadow_offset=}, {self.margin=}."

        # create mask to round edges of terminal window
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

        self.window_layer = Image.new(
            "RGBA", (self.img_width, self.img_height), (0, 0, 0, 0)
        )
        self.window_layer.paste(terminal, (self.margin, self.margin), self.mask)

    def render_text_layer(self, code, style="monokai"):
        # assert self.window_layer, "create window image before rendering text"

        formatter = TokenFormatter(style=style)
        highlight(code, PythonLexer(), formatter)

        wrapped_lines = get_wrapped_lines(
            formatter.result,
            self.columns,
            self.rows,
        )

        terminal = Image.new(
            "RGBA",
            (self.window_width, self.window_height),
            (40, 42, 54),
        )
        terminal_draw = ImageDraw.Draw(terminal)

        # place text
        y = self.padding + self.bar_height
        for line in wrapped_lines:
            x = self.padding
            for token, color in line:
                terminal_draw.text((x, y), token, font=self.font, fill=color)
                x += self.font.getlength(token)
            y += self.line_height

        # create mask to round edges of terminal window
        mask = Image.new("L", (self.window_width, self.window_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, self.window_width, self.window_height],
            radius=self.corner_radius,
            fill=255,
        )
        mask_draw.rectangle([(0, 0), (self.window_width, self.bar_height)], fill=0)

        self.text_layer = Image.new(
            "RGBA",
            (self.window_width, self.window_height - self.bar_height),
            (0, 0, 0, 0),
        )
        self.text_layer.paste(terminal, (self.margin, self.margin), mask)

    def composit_layers(self, blur=0.0):
        """Composit all layers."""
        self.final_image = self.bg_layer
        self.final_image.alpha_composite(self.shadow_layer)
        self.final_image.alpha_composite(self.window_layer)
        self.final_image.alpha_composite(self.text_layer)
        self.final_image = self.final_image.filter(ImageFilter.GaussianBlur(blur))

    def save_image(self, filename="rendered_code.png"):
        self.final_image.convert("RGBA").save(filename, "PNG")
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
    renderer.render_background_layer("green")
    renderer.render_shadow_layer()
    renderer.render_window_layer()
    renderer.render_text_layer(code, style=args.theme)

    renderer.composit_layers(blur=0.5)
    renderer.save_image(args.output)


###############################################################################


def create_uniform_background(width, height, color="white"):
    color = any_color_to_rgba(color)
    return Image.new("RGBA", (width, height), (color))


def create_gradient_background(width, height, start_color="coral", end_color="salmon"):
    import math

    start_color = any_color_to_rgba(start_color)
    end_color = any_color_to_rgba(end_color)

    image = Image.new("RGBA", (width, height))
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


def any_color_to_rgba(color):
    """Converts any color name (str), RGB, or RGBA tuple to RGBA.

    Find a list of colors at https://www.w3.org/TR/css-color-3/#svg-color
    For example, color can be \"skyblue\", (255, 126, 0), or (0, 255, 80, 0).
    """
    if isinstance(color, str):
        try:
            return ImageColor.getcolor(color, "RGBA")
        except ValueError:
            pass

    if isinstance(color, (tuple, list)):
        if len(color) == 3:
            color = tuple(color) + (0,)
        if len(color) == 4:
            if all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                return color

    raise ValueError(
        "Specify a valid color name, or an RGB/RGBA integer tuple with 0-255 range."
    )


if __name__ == "__main__":
    main()
