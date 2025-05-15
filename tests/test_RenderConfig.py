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


# def test_invalid_font_path():
#     invalid_font_path = "./invalid/font/path.ttf"
#     with pytest.raises(FileNotFoundError):
#         RenderConfig(font_path=invalid_font_path)


# def test_default_font_path():
#     RenderConfig(font_path=None)


def test_invalid_style(monkeypatch):

    def mock_get_all_styles():
        return available_styles

    def mock_get_style_by_name(style_name):
        raise ClassNotFound("Style not found")

    monkeypatch.setattr("pycheese.render.get_all_styles", mock_get_all_styles)
    monkeypatch.setattr("pycheese.render.get_style_by_name", mock_get_style_by_name)

    with pytest.raises(StyleNotFoundError) as exc_info:
        RenderConfig(style=invalid_style)

    assert invalid_style in str(exc_info.value)


def test_text_background_color(monkeypatch):
    # 1: Style has a background_color
    monkeypatch.setattr(
        "pycheese.render.get_style_by_name", mock_get_style_by_name_black_bg
    )

    config = RenderConfig(style="monokai")
    assert config.text_background_color == "black"

    # 2: Style does not have a background_color
    monkeypatch.setattr(
        "pycheese.render.get_style_by_name", mock_get_style_by_name_no_bg
    )

    config_no_bg = RenderConfig(style="monokai")
    assert config_no_bg.text_background_color == "white"


def test_default_text_color_calculation(monkeypatch):
    def mock_any_color_to_rgba(color):
        if color == "white":
            return 255, 255, 255, 0
        elif color == "black":
            return 0, 0, 0, 0
        return 0, 0, 0, 0

    monkeypatch.setattr("pycheese.render.any_color_to_rgba", mock_any_color_to_rgba)
    monkeypatch.setattr(
        "pycheese.render.get_style_by_name", mock_get_style_by_name_no_bg
    )

    # text color defaults to black if the text background is set to white
    config_white = RenderConfig(style="monokai", text_background_color="white")
    assert config_white.default_text_color == (0, 0, 0)

    # text color defaults to white if the text background is set to black
    config_black = RenderConfig(style="monokai", text_background_color="black")
    assert config_black.default_text_color == (255, 255, 255)

    # text color defaults to black b/c default bg color is white if set to None
    config = RenderConfig(style="monokai", text_background_color=None)
    assert config.default_text_color == (0, 0, 0)
