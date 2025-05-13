import pytest

from pycheese import StyleNotFoundError

invalid_style = "invalid_style"
available_styles = ("monokai", "solarized", "gruvbox")


def test_StyleNotFoundError_attributes():

    with pytest.raises(StyleNotFoundError) as exc_info:
        raise StyleNotFoundError(invalid_style, available_styles)

    assert exc_info.value.style_name == invalid_style
    assert exc_info.value.available_styles == available_styles
