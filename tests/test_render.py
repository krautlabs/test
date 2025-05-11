from pathlib import Path

import pytest
from pygments.util import ClassNotFound

from codevista import RenderConfig, StyleNotFoundError

invalid_style = "invalid_style"
available_styles = ("monokai", "solarized", "gruvbox")


def test_StyleNotFoundError_attributes():

    with pytest.raises(StyleNotFoundError) as exc_info:
        raise StyleNotFoundError(invalid_style, available_styles)

    assert exc_info.value.style_name == invalid_style
    assert exc_info.value.available_styles == available_styles


def test_RenderConfig_invalid_font_path():
    invalid_font_path = "./invalid/font/path.ttf"
    with pytest.raises(FileNotFoundError):
        RenderConfig(font_path=invalid_font_path)


def test_RenderConfig_invalid_style(monkeypatch):

    def mock_get_all_styles():
        return available_styles

    def mock_get_style_by_name(style_name):
        raise ClassNotFound("Style not found")

    monkeypatch.setattr("codevista.render.get_all_styles", mock_get_all_styles)
    monkeypatch.setattr("codevista.render.get_style_by_name", mock_get_style_by_name)

    with pytest.raises(StyleNotFoundError) as exc_info:
        RenderConfig(style=invalid_style)

    assert invalid_style in str(exc_info.value)


# # Test 4: Test that `text_background_color` is set correctly (default to style's background color or white)
# def test_text_background_color_default():
#     # Mock style with a background color
#     class MockStyle:
#         background_color = "black"
#
#     def mock_get_style_by_name(style_name):
#         return MockStyle()
#
#     global get_style_by_name
#     get_style_by_name = mock_get_style_by_name
#
#     config = RenderConfig(style="monokai")
#     assert config.text_background_color == "black"
#
#     # Now test with a style that doesn't have background_color
#     class MockStyleNoBackgroundColor:
#         pass
#
#     def mock_get_style_by_name_no_bg(style_name):
#         return MockStyleNoBackgroundColor()
#
#     get_style_by_name = mock_get_style_by_name_no_bg
#     config_no_bg = RenderConfig(style="monokai")
#     assert config_no_bg.text_background_color == "white"
#
#
# # Test 5: Test default text color calculation based on background color
# def test_default_text_color_calculation():
#     # Mocking the color conversion to return specific RGBA values
#     def mock_any_color_to_rgba(color):
#         if color == "white":
#             return 255, 255, 255, 1  # RGBA for white
#         elif color == "black":
#             return 0, 0, 0, 1  # RGBA for black
#         return 0, 0, 0, 1
#
#     global any_color_to_rgba
#     any_color_to_rgba = mock_any_color_to_rgba
#
#     # Test when text_background_color is set to "white"
#     config = RenderConfig(style="monokai", text_background_color="white")
#     assert config.default_text_color == (0, 0, 0)  # Text color should be black
#
#     # Test when text_background_color is set to "black"
#     config = RenderConfig(style="monokai", text_background_color="black")
#     assert config.default_text_color == (255, 255, 255)  # Text color should be white
#
#
# # Test 6: Test that if `default_text_color` is None, it gets set to the correct value based on `text_background_color`
# def test_default_text_color_when_none():
#     # Mock style with a background color
#     class MockStyle:
#         background_color = "black"
#
#     def mock_get_style_by_name(style_name):
#         return MockStyle()
#
#     global get_style_by_name
#     get_style_by_name = mock_get_style_by_name
#
#     config = Rende
