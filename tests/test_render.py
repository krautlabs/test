from pathlib import Path

import pytest
from pygments.util import ClassNotFound

from pycheese import RenderConfig, StyleNotFoundError

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


# def test_RenderConfig_invalid_font_path():
#     invalid_font_path = "./invalid/font/path.ttf"
#     with pytest.raises(FileNotFoundError):
#         RenderConfig(font_path=invalid_font_path)
#

# def test_RenderConfig_valid_font_path():
#     valid_font_path = "fonts/JetBrainsMono-Regular.ttf"
#     with pytest.raises(FileNotFoundError):
#         RenderConfig(font_path=invalid_font_path)
