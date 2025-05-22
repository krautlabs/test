import argparse
import os
import tomllib
from importlib.resources import as_file, files
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlretrieve

from PIL import ImageFont


def get_font_config_resource():
    return files("pycheese") / "fonts" / "font_config.toml"


class Font:
    def __init__(self, family_name, config):
        self.family_name = family_name
        self.font_paths = None
        self.origin = None
        self.font_dir = files("pycheese") / "fonts"
        self._set_paths_and_origin(config)
        self.ImageFonts = {}

    def _set_paths_and_origin(self, config):
        try:
            family_config = config[self.family_name]
        except KeyError:
            raise ValueError(f'Font "{self.family_name}" not found in config.')
        try:
            self.font_paths = family_config["styles"]
            self.origin = family_config["origin"]["url"]
        except KeyError as e:
            raise ValueError(f"Missing key during Font initialization: {e}")
        self._set_full_font_paths()

    def _set_full_font_paths(self):
        with as_file(self.font_dir) as font_dir:
            for style, filename in self.font_paths.items():
                font_path = Path(font_dir) / filename
                if not font_path.exists():
                    raise FileNotFoundError(f"Font file not found: {font_path}")
                self.font_paths[style] = font_path

    def get_ImageFont(self, size: int, style: str = "regular"):
        if len(self.ImageFonts) > 20:  # prune cache
            self.ImageFonts = {}
        if not (style, size) in self.ImageFonts:
            print("generating", style, size)
            self.ImageFonts[(style, size)] = ImageFont.truetype(
                self.font_paths[style], size
            )
        return self.ImageFonts[(style, size)]

    @classmethod
    def from_config_file(cls, family_name: str, path: Path):
        with as_file(path) as config_path:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
                return cls(family_name, config)


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


def font_paths(font_family: str):
    """Returns absolute font paths for every style of the family."""
    font_config = load_font_config()
    if not font_family in font_config:
        raise ValueError(f'Font family "{font_family}" not defined in font config.')

    font_paths_dict = font_config[font_family]["styles"].copy()
    font_resources = files("pycheese") / "fonts"

    with as_file(font_resources) as font_path:
        for style, filename in font_paths_dict.items():
            font_file_path = Path(font_path) / filename
            font_paths_dict[style] = font_file_path

    return font_paths_dict


def load_font_config():
    with as_file(get_font_config_resource()) as config_path:
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
            raise ValueError(f'Font "{font_family}" not defined in font config.')
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
