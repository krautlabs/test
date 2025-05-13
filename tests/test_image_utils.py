import pytest
from PIL import Image

from pycheese.utils.image import create_uniform_background


def test_create_uniform_background_default_color():
    width, height = 100, 100
    image = create_uniform_background(width, height)

    assert image.size == (width, height)
    assert image.mode == "RGBA"
    assert image.getpixel((0, 0)) == (255, 255, 255, 255)
