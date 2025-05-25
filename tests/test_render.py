from pathlib import Path

import pytest
from PIL import Image, ImageColor
from pygments.util import ClassNotFound

from pycheese import Render, RenderConfig, StyleNotFoundError

invalid_style = "invalid_style"
available_styles = ("monokai", "solarized", "gruvbox")


class MockStyleBlackBackground:
    background_color = "black"


class MockStyleNoBackground:
    pass


def mock_get_style_by_name_no_bg(style_name):
    return MockStyleNoBackground()


def mock_get_style_by_name_black_bg(style_name):
    return MockStyleBlackBackground()


def test_StyleNotFoundError_attributes():

    with pytest.raises(StyleNotFoundError) as exc_info:
        raise StyleNotFoundError(invalid_style, available_styles)

    assert exc_info.value.style_name == invalid_style
    assert exc_info.value.available_styles == available_styles


@pytest.fixture
def sample_config():
    #     class DummyFont:
    #         def get_ImageFont(self, size, style):
    #             from PIL import ImageFont
    #
    #             return ImageFont.load_default()

    return RenderConfig(
        columns=80,
        rows=24,
        padding=10,
        margin=20,
        line_spacing=1.5,
        bar_height=30,
        font_family="JetBrainsMono",
        font_size=12,
        corner_radius=6,
        default_text_color=(0, 0, 0),
        text_background_color="white",
        style="monokai",
        shadow_offset=10,
        shadow_blur=6,
        shadow_color="black",
        shadow_alpha=180,
        first_bg_color="white",
        second_bg_color=None,
        post_blur=0.0,
    )


@pytest.fixture
def render_instance(sample_config):
    return Render(sample_config)


def test_image_dimensions(render_instance):
    r = render_instance
    assert r.img_width == r.window_width + 2 * r.cfg.margin
    assert r.img_height == r.window_height + 2 * r.cfg.margin


def test_render_uniform_background_layer(render_instance):
    color_name = "blue"
    render_instance.render_background_layer(color_name)
    bg_layer = render_instance.bg_layer
    assert isinstance(bg_layer, Image.Image)
    assert bg_layer.size == (
        render_instance.img_width,
        render_instance.img_height,
    )
    assert bg_layer.getpixel((0, 0)) == ImageColor.getcolor(color_name, "RGBA")


# def test_render_gradient_background_layer(render_instance):
#     first_color = "blue"
#     second_color = "red"
#     render_instance.render_background_layer(first_color, second_color)
#     bg_layer = render_instance.bg_layer
#     assert isinstance(bg_layer, Image.Image)
#     assert bg_layer.size == (
#         render_instance.img_width,
#         render_instance.img_height,
#     )
#     assert bg_layer.getpixel((0, 0)) == ImageColor.getcolor(first_color, "RGBA")
#     assert bg_layer.getpixel(
#         (render_instance.img_width - 1, render_instance.img_height - 1)
#     ) == (254, 0, 0, 255)
#


def test_render_shadow_layer(render_instance):
    render_instance.render_shadow_layer()
    assert isinstance(render_instance.shadow_layer, Image.Image)


def test_render_titlebar_layer(render_instance):
    render_instance.render_titlebar_layer()
    assert isinstance(render_instance.titlebar_layer, Image.Image)


def test_render_text_layer(render_instance):
    render_instance.render_text_layer("print('Hello')", style="monokai")
    assert isinstance(render_instance.text_layer, Image.Image)


def test_composit_layers(render_instance):
    r = render_instance
    r.render_background_layer("white")
    r.render_shadow_layer()
    r.render_titlebar_layer()
    r.render_text_layer("print('test')")
    r.composit_layers()
    assert isinstance(r.final_image, Image.Image)


def test_full_render_flow(render_instance):
    render_instance.render("print('full test')")
    assert render_instance.final_image is not None


def test_save_image(tmp_path, render_instance):
    render_instance.render("print('save')")
    output_path = tmp_path / "test_output.png"
    render_instance.save_image(str(output_path))
    assert output_path.exists()
    assert output_path.suffix == ".png"
