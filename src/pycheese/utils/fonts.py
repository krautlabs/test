import argparse
import os
import tomllib
from importlib.resources import as_file, files
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlretrieve

FONT_CONFIG = "font_config.toml"
STYLES = ["regular", "bold", "italic", "bold_italic"]


def join_base_and_filename(base: str, filename: str):
    """Join a path/URL with a filename.

    Parameters:
        base (str): The base path or URL.
        filename (str): The filename or relative path to append.

    Returns:
        str: The combined path or URL.
    """
    if urlparse(base).scheme in ("http", "https"):
        return urljoin(base, filename)
    else:
        return os.path.join(base, filename)


def find_font(name):
    config = load_font_config()
    if name in config:
        print(f"found font {name}")


def load_font_config():
    config_resource = files("pycheese") / "fonts" / FONT_CONFIG
    with as_file(config_resource) as config_path:
        with open(config_path, "rb") as f:
            return tomllib.load(f)


def list_fonts(config):
    for family, info in config.items():
        origin = info.get("origin", {}).get("url", "?")
        print(f"{family} (origin: {origin}):")
        for style, filename in info["styles"].items():
            print(f"  {style:12} {filename}")


def update_font(filename, url):
    font_resources = files("pycheese") / "fonts"

    with as_file(font_resources) as font_path:
        font_dir = Path(font_path)
        font_file_path = font_dir / filename

        if not os.path.isdir(font_dir):
            raise FileNotFoundError("The fonts/ directory does not exist.")

        if font_file_path.exists():
            print(f"Skipping download, font already exists: {filename}")
            return

        download_font(source=url, target=font_file_path)


def download_font(source, target):
    print(f"{source=}, {target=}")
    try:
        urlretrieve(source, target)
        print(f"Font saved to: {target}")
    except Exception as e:
        print(f"Failed to download {source}: {e}")


def update_fonts(config, font_names):
    for family in font_names:
        if family not in config:
            raise ValueError(f"Font {family} not declared in font_config.toml")
        base = config[family].get("origin", {}).get("url", None)
        if base:
            for style, filename in config[family]["styles"].items():
                url = join_base_and_filename(base, filename)
                update_font(filename, url)


def update_all_fonts(config):
    font_names = [f for f in config]
    update_fonts(config, font_names)


def main():
    parser = argparse.ArgumentParser(description="Font Downloader")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List available fonts")
    group.add_argument("--all", action="store_true", help="Update all fonts")
    group.add_argument(
        "--fonts", nargs="+", help="Update specific fonts by style or filename"
    )

    args = parser.parse_args()
    config = load_font_config()

    if args.list:
        list_fonts(config)
    elif args.all:
        update_all_fonts(config)
    elif args.fonts:
        update_fonts(config, args.fonts)


if __name__ == "__main__":
    main()
