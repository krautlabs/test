import argparse
import os
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont
from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name


@dataclass
class RenderConfig:
    font_path: str = "./fonts/JetBrainsMono-Regular.ttf"
    style: str = "monokai"
    font_size: int = 20
    padding: int = 20
    margin: int = 20
    line_spacing: float = 1.4
    rows: int = 24
    columns: int = 80
    corner_radius: int = 16
    post_blur: float = 0.5
    bar_height: int = 30
    shadow_offset: int = 10
    shadow_blur: int = 6
    shadow_color: str = "black"
    shadow_alpha: int = 180


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
    def __init__(self, code, config: RenderConfig):
        self.code = code
        self.cfg = config

        self.font = None
        self.line_height = None
        self.bar_height = 30

        self.bg_layer = None
        self.shadow_layer = None
        self.text_layer = None
        self.titlebar_layer = None
        self.final_image = None

        self.shadow_offset = 10
        self.shadow_blur = 6
        self.shadow_color = "black"
        self.shadow_alpha = 180

        self._init_font_properties()
        self._init_image_properties()

    def _init_font_properties(self):
        self.font = ImageFont.truetype(self.cfg.font_path, self.cfg.font_size)
        self.line_height = int(self.cfg.font_size * self.cfg.line_spacing)
        self.char_width = self.font.getlength("M")

    def _init_image_properties(self):
        self.window_width = int(
            self.cfg.columns * self.char_width + 2 * self.cfg.padding
        )
        self.window_height = int(
            self.cfg.rows * self.line_height + 2 * self.cfg.padding + 30
        )
        self.img_width = int(self.window_width + 2 * self.cfg.margin)
        self.img_height = int(self.window_height + 2 * self.cfg.margin)

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
                self.cfg.margin + shadow_offset,
                self.cfg.margin + shadow_offset,
                self.cfg.margin + self.window_width + shadow_offset,
                self.cfg.margin + self.window_height + shadow_offset,
            ],
            radius=corner_radius,
            fill=(rgba),
        )
        self.shadow_layer = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))

    def render_titlebar_layer(self, color=(30, 30, 30)):
        """Render a stylized terminal window title bar resembling macOS."""
        # assert (
        #     self.shadow_offset <= self.margin
        # ), f"{self.shadow_offset=}, {self.margin=}."

        terminal = Image.new("RGBA", (self.window_width, self.bar_height), (0, 0, 0, 0))
        terminal_draw = ImageDraw.Draw(terminal)

        # Draw top bar with traffic lights
        terminal_draw.rounded_rectangle(
            [0, 0, self.window_width, self.window_height],
            radius=self.cfg.corner_radius,
            fill=color,
        )
        traffic_colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
        for i, color in enumerate(traffic_colors):
            terminal_draw.ellipse(
                [(self.cfg.padding + i * 20, 8), (self.cfg.padding + i * 20 + 12, 20)],
                fill=color,
            )
        self.titlebar_layer = Image.new(
            "RGBA", (self.img_width, self.img_height), (0, 0, 0, 0)
        )
        self.titlebar_layer.paste(terminal, (self.cfg.margin, self.cfg.margin))

    def render_text_layer(self, code, style="monokai"):
        """Render text area according to style on top of solid background."""

        formatter = TokenFormatter(style=style)
        highlight(code, PythonLexer(), formatter)

        wrapped_lines = get_wrapped_lines(
            formatter.result,
            self.cfg.columns,
            self.cfg.rows,
        )

        terminal = Image.new(
            "RGBA",
            (self.window_width, self.window_height),
            (40, 42, 54),
        )
        terminal_draw = ImageDraw.Draw(terminal)

        # place text
        y = self.cfg.padding + self.cfg.bar_height
        for line in wrapped_lines:
            x = self.cfg.padding
            for token, color in line:
                terminal_draw.text((x, y), token, font=self.font, fill=color)
                x += self.font.getlength(token)
            y += self.line_height

        # create mask to round edges of terminal window
        mask = Image.new("L", (self.window_width, self.window_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, self.window_width, self.window_height],
            radius=self.cfg.corner_radius,
            fill=255,
        )
        self.text_layer = Image.new(
            "RGBA",
            (self.img_width, self.img_height),
            (0, 0, 0, 0),
        )
        self.text_layer.paste(terminal, (self.cfg.margin, self.cfg.margin), mask)

    def composit_layers(self, blur=0.0):
        """Composit all layers."""
        self.final_image = self.bg_layer.copy()
        self.final_image.alpha_composite(self.shadow_layer)
        self.final_image.alpha_composite(self.text_layer)
        self.final_image.alpha_composite(self.titlebar_layer)
        self.final_image = self.final_image.filter(ImageFilter.GaussianBlur(blur))

    def render(self):
        if self.bg_layer is None:
            self.render_background_layer()
        if self.shadow_layer is None:
            self.render_shadow_layer(
                shadow_offset=self.cfg.shadow_offset,
                shadow_blur=self.cfg.shadow_blur,
                shadow_color=self.cfg.shadow_color,
                shadow_alpha=self.cfg.shadow_alpha,
                corner_radius=self.cfg.corner_radius,
            )
        if self.titlebar_layer is None:
            self.render_titlebar_layer()
        if self.text_layer is None:
            self.render_text_layer(self.code, style=self.cfg.style)
        self.composit_layers(blur=self.cfg.post_blur)

    def save_image(self, filename="rendered_code.png"):
        if self.final_image is None:
            raise ValueError("You have to run .render() to create an image first.")
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

    config = RenderConfig(
        columns=args.columns,
        rows=args.rows,
        font_path=args.font,
    )
    renderer = Renderer(
        code=code,
        config=config,
    )

    # individual layers can be manually rendered
    # renderer.render_background_layer(first_color=(0, 0, 0, 0))

    # Monokai-style purple gradient (dark to light purple)
    end_color = (93, 80, 124)
    start_color = (151, 125, 201)
    renderer.render_background_layer(first_color=start_color, second_color=end_color)
    renderer.render()
    renderer.save_image(args.output)

    # import numpy as np
    #
    # final_frames = 10
    # for i, j in enumerate(np.cumsum(np.random.choice([3, 5, 7], size=200))):
    #     if j > len(code):
    #         j = len(code)
    #         final_frames -= 1
    #     filename = f"gif/out{i:03d}.png"
    #     renderer.render_text_layer(code[:j])
    #     renderer.composit_layers(blur=0.5)
    #     renderer.save_image(filename)
    #     if final_frames < 1:
    #         break
    # magick -delay 20 -loop 0 gif/*.png output.gif

    # Step 1: Create a palette (for good color quantization)
    # ffmpeg -y -i gif/out%02d.png -vf palettegen palette.png

    # Step 2: Use the palette to make the GIF
    # ffmpeg -i gif/out%03d.png -i palette.png -lavfi "fps=10 [x]; [x][1:v] paletteuse" output.gif

    # ffmpeg -framerate 1 -i gif/out%02d.png -c:v libx264 -r 60 -pix_fmt yuv420p output.mp4


###############################################################################


def create_uniform_background(width, height, color="white"):
    color = any_color_to_rgba(color)
    return Image.new("RGBA", (width, height), color)


def create_gradient_background(width, height, start_color="coral", end_color="salmon"):
    import math

    start_color = any_color_to_rgba(start_color)
    end_color = any_color_to_rgba(end_color)

    image = Image.new("RGBA", (width, height))
    angle_rad = math.radians(60)

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
            color = tuple(color) + (255,)
        if len(color) == 4:
            if all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                return color

    raise ValueError(
        "Specify a valid color name, or an RGB/RGBA integer tuple with 0-255 range."
    )


if __name__ == "__main__":
    main()
