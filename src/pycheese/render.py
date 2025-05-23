import os
import textwrap
from dataclasses import dataclass, field
from importlib.resources import as_file, files
from pathlib import Path
from typing import Optional

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont
from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexers import PythonLexer
from pygments.styles import get_all_styles, get_style_by_name
from pygments.util import ClassNotFound

from pycheese.args import get_args
from pycheese.utils.fonts import Font, font_paths, get_font_config_resource
from pycheese.utils.image import (
    any_color_to_rgba,
    create_gradient_background,
    create_uniform_background,
)
from pycheese.utils.linewrap import tokenize, wrap_tokens


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
    style: str = "monokai"
    font_family: str = "JetBrainsMono"
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
    font: Optional[Font] = field(init=False)

    def __post_init__(self):
        self._validate_style()  # validate theme
        self._set_font()

    def _set_font(self):
        self.font = Font.from_config_file(
            self.font_family,
            path=get_font_config_resource(),
        )
        self.line_height = int(self.font_size * self.line_spacing)
        self.char_width = self.font.get_ImageFont(size=self.font_size).getlength("M")

    def _validate_style(self):
        """Validate pygments style/theme."""
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


class Render:
    def __init__(self, config: RenderConfig):
        self.cfg = config

        self.bar_height = 30

        self.bg_layer = None
        self.shadow_layer = None
        self.text_layer = None
        self.titlebar_layer = None
        self.final_image = None

        self._code = None

        self._init_image_properties()

    def _init_image_properties(self):
        self.window_width = int(
            self.cfg.columns * self.cfg.char_width + 2 * self.cfg.padding
        )
        self.window_height = int(
            self.cfg.rows * self.cfg.line_height + 2 * self.cfg.padding + 30
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

        tokens = tokenize(
            code,
            lexer=PythonLexer(),
            style=style,
            default_text_color=self.cfg.default_text_color,
        )
        wrapped_lines = wrap_tokens(tokens, width=self.cfg.columns)

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
            for token, color, font_style, *_ in line:
                image_font = self.cfg.font.get_ImageFont(
                    size=self.cfg.font_size, style=font_style
                )
                terminal_draw.text((x, y), token, font=image_font, fill=color)
                x += image_font.getlength(token)
            y += self.cfg.line_height

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

    def render(self, code):
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
        if self.text_layer is None or self._code != code:
            self._code = code
            self.render_text_layer(code, style=self.cfg.style)
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

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
    else:
        code = sys.stdin.read()

    # if not Path(args.font).exists():
    #     raise FileNotFoundError("Font file not found. Provide a valid TTF file.")

    config = RenderConfig(
        columns=args.columns,
        rows=args.rows,
        font_family=args.font,
        style=args.style,
    )

    renderer = Render(
        config=config,
    )

    # Monokai-style purple gradient (dark to light purple)
    # end_color = (93, 80, 124)
    # start_color = (151, 125, 201)
    # renderer.render_background_layer(first_color=start_color, second_color=end_color)

    renderer.render(code=code)
    renderer.save_image(args.output)


if __name__ == "__main__":
    main()
