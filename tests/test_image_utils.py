import pytest
from PIL import Image

from pycheese.utils.image import (
    Color,
    create_gradient_background,
    create_uniform_background,
)


def rgba_colors_are_close(c1, c2, tolerance=2):
    return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))


def test_create_uniform_background_default_color():
    width, height = 100, 100
    image = create_uniform_background(width, height)

    assert image.size == (width, height)
    assert image.mode == "RGBA"
    assert image.getpixel((0, 0)) == (255, 255, 255, 255)


def test_gradient_background_basic_properties():
    width, height = 100, 100
    start_color = (255, 127, 80, 255)  # "coral"
    end_color = (250, 127, 113, 255)  # "salmon"

    image = create_gradient_background(width, height, start_color, end_color)

    assert image.size == (width, height)
    assert rgba_colors_are_close(image.getpixel((0, 0)), start_color)
    assert rgba_colors_are_close(image.getpixel((width - 1, height - 1)), end_color)


def test_repr():
    color = Color.from_any_color("white")
    assert repr(color) == "Color(255, 255, 255, 255)"


def test_from_named_color():
    color = Color.from_any_color("white")
    assert color.rgb == (255, 255, 255)
    assert color.alpha == 255
    assert color.hex == "#ffffff"
    assert color.name == "white"


def test_from_hex():
    color = Color.from_any_color("#ff0078")
    assert color.rgb == (255, 0, 120)
    assert color.hex == "#ff0078"
    assert color.name is None


def test_from_rgb_tuple():
    color = Color.from_any_color((255, 255, 255))
    assert color.rgb == (255, 255, 255)
    assert color.alpha == 255
    assert color.hexa == "#ffffffff"
    assert color._name == None
    assert color.name == "white"


def test_from_rgba_tuple():
    color = Color.from_any_color((10, 20, 30, 128))
    assert color.rgba == (10, 20, 30, 128)
    assert color.hexa == "#0a141e80"


def test_copy_color():
    original = Color.from_any_color("navy")
    copy = Color.from_any_color(original)
    assert copy.rgb == original.rgb
    assert copy.alpha == original.alpha
    assert copy.name == original.name
    assert copy is not original


def test_invalid_tuple_length():
    with pytest.raises(ValueError):
        Color.from_any_color((255,))


def test_invalid_type():
    with pytest.raises(TypeError):
        Color.from_any_color(42)


def test_invalid_type():
    with pytest.raises(TypeError):
        Color.from_any_color(None)


@pytest.mark.parametrize(
    "r, g, b, a",
    [
        (256, 255, 255, 255),
        (-1, 255, 255, 255),
        (255, 256, 255, 255),
        (255, -1, 255, 255),
        (255, 255, 256, 255),
        (255, 255, -1, 255),
        (255, 255, 255, 256),
        (255, 255, 255, -1),
    ],
)
def test_color_channels_out_of_range(r, g, b, a):
    with pytest.raises(ValueError):
        Color(r, g, b, a)
