import os

import pytest

from pycheese.utils.fonts import join_base_and_filename


@pytest.mark.parametrize(
    "base, filename, expected",
    [
        ("https://example.com/path/", "file.txt", "https://example.com/path/file.txt"),
        ("http://example.com/dir", "page.html", "http://example.com/page.html"),
        ("/home/user/docs", "test.txt", os.path.join("/home/user/docs", "test.txt")),
        ("C:\\Users\\Alice", "test.pdf", os.path.join("C:\\Users\\Alice", "test.pdf")),
    ],
)
def test_join_base_and_filename(base, filename, expected):
    assert join_base_and_filename(base, filename) == expected
