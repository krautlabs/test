import argparse
import os
import textwrap
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont
from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexers import PythonLexer
from pygments.styles import get_all_styles, get_style_by_name
from pygments.util import ClassNotFound

from pycheese.args import get_args
from pycheese.utils.fonts import find_font
from pycheese.utils.image import (
    any_color_to_rgba,
    create_gradient_background,
    create_uniform_background,
)


class StyleNotFoundError(ClassNotFound):
    def __init__(self, style_name, available_styles):
        message = (
            f"Invalid style '{style_name}'.\n"
            f"Available styles are: {', '.join(available_styles)}"
        )
        super().__init__(message)
        self.style_name = style_name
        self.available_styles = available_styles


@dataclass
class RenderConfig:
    font_path: str | None = None
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
    text_background_color: str | None = None
    default_text_color: str | None = None

    def __post_init__(self):
        self.validate_font_path()
        self.validate_style()

    def validate_font_path(self):
        if self.font_path is None:
            resource = files("pycheese") / "fonts" / "JetBrainsMono-Regular.ttf"
            with as_file(resource) as font_path:
                self.font_path = Path(resource)

        if not Path(self.font_path).is_file():
            raise FileNotFoundError(f"Font file not found: {self.font_path}")

    def validate_style(self):
        try:
            style_obj = get_style_by_name(self.style)
        except ClassNotFound:
            available = list(get_all_styles())
            raise StyleNotFoundError(self.style, available)

        if self.text_background_color is None:
            try:
                self.text_background_color = style_obj.background_color
            except AttributeError:
                print(
                    f"Style {self.style} has no background_color attribute, using white."
                )
                self.text_background_color = "white"

        if self.default_text_color is None:
            r, g, b, _ = any_color_to_rgba(self.text_background_color)
            self.default_text_color = (255 - r, 255 - g, 255 - b)


# Custom formatter to extract tokens with styles
class TokenFormatter(Formatter):
    def __init__(self, default_text_color, **options):
        super().__init__(**options)
        self.styles = {}
        self.result = []
        self.default_text_color = default_text_color
        style = get_style_by_name(options.get("style", "monokai"))
        for token, style_def in style:
            if style_def["color"]:
                self.styles[token] = "#" + style_def["color"]
            else:
                self.styles[token] = self.default_text_color

    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            color = self.styles.get(ttype, self.default_text_color)
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


class Render:
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
            # outline="green",
            # width=2,
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

    def render_text_layer(self, code, style="monokai", background_color=None):
        """Render text area according to style on top of solid background."""

        formatter = TokenFormatter(
            default_text_color=self.cfg.default_text_color,
            style=style,
        )
        highlight(code, PythonLexer(), formatter)

        wrapped_lines = get_wrapped_lines(
            formatter.result,
            self.cfg.columns,
            self.cfg.rows,
        )

        if background_color is None:
            background_color = self.cfg.text_background_color
        background_color = any_color_to_rgba(background_color)

        terminal = Image.new(
            "RGBA",
            (self.window_width, self.window_height),
            background_color,
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
    args = get_args()

    # if not Path(args.font).exists():
    #     raise FileNotFoundError("Font file not found. Provide a valid TTF file.")
    #     print(list(get_all_styles()))

    if not Path(args.source_file).exists() or not args.source_file.endswith(".py"):
        raise FileNotFoundError("The source file must exist and be a .py file.")

    # if not Path(args.font).exists():
    #     raise FileNotFoundError("Font file not found. Provide a valid TTF file.")

    with open(args.source_file, "r", encoding="utf-8") as f:
        code = f.read()

    config = RenderConfig(
        columns=args.columns,
        rows=args.rows,
        font_path=args.font,
        style=args.style,
    )
    renderer = Render(
        code=code,
        config=config,
    )

    # individual layers can be manually rendered
    # renderer.render_background_layer(first_color=(0, 0, 0, 0))

    # Monokai-style purple gradient (dark to light purple)
    end_color = (93, 80, 124)
    start_color = (151, 125, 201)
    # renderer.render_background_layer(first_color=start_color, second_color=end_color)
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


if __name__ == "__main__":
    main()
