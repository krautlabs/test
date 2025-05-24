import pytest
from PIL import Image

from pycheese.utils.image import create_gradient_background, create_uniform_background


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
