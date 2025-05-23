import argparse
import os
import tomllib
from enum import Enum
from importlib.resources import as_file, files
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlretrieve

from PIL import ImageFont


def get_font_config_resource():
    return files("pycheese") / "fonts" / "font_config.toml"


class FontStyle(Enum):
    REGULAR = "regular"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bolditalic"


class Font:
    def __init__(self, family_name, config):
        self.family_name = family_name
        self.font_paths = None
        self.origin = None
        self.external_link = False
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
            if family_config["origin"]["type"] == "local_path":
                self.external_link = True
            self.origin = family_config["origin"]["url"]
        except KeyError as e:
            raise ValueError(f"Missing key during Font initialization: {e}")
        self._set_full_font_paths()

    def _set_full_font_paths(self):
        if self.external_link:
            font_orig = Path(self.origin)
        else:
            font_orig = self.font_dir
        with as_file(font_orig) as font_dir:
            for style, filename in self.font_paths.items():
                font_path = Path(font_dir) / filename
                if not font_path.exists():
                    raise FileNotFoundError(f"Font file not found: {font_path}")
                self.font_paths[style] = font_path

    def get_ImageFont(self, size: int, style: str = "regular"):
        if len(self.ImageFonts) > 20:  # prune cache
            self.ImageFonts = {}
        if not (style, size) in self.ImageFonts:
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


def save_font_config(config: dict):
    import tomli_w

    with as_file(get_font_config_resource()) as config_path:
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)


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
    # TODO: check that source is a URL
    print(f"{source=}, {target=}")
    try:
        urlretrieve(source, target)
        print(f"Font saved to: {target}")
    except Exception as e:
        print(f"Failed to download {source}: {e}")


def update_fonts(config, font_names):
    for family in font_names:
        if family not in config:
            raise ValueError(f'Font "{family}" not defined in font config.')
        if config[family]["origin"]["type"] == "local_path":
            print(f'Font "{family}" is local, no update needed.')
            continue
        base = config[family].get("origin", {}).get("url", None)
        if base:
            for style, filename in config[family]["styles"].items():
                url = join_base_and_filename(base, filename)
                update_font(filename, url)


def update_all_fonts(config):
    font_names = [f for f in config]
    update_fonts(config, font_names)


def font_to_toml_dict(font_path: str) -> dict:
    font_path = Path(font_path).expanduser().resolve()

    directory = font_path.parent
    filename = font_path.name

    # Extract font family name from the filename (assumes Regular is part of the name)
    if not filename.endswith("Regular.ttf"):
        raise ValueError(
            "Expected the regular variant filename to end with 'Regular.ttf'"
        )

    font_family = filename.replace("-Regular.ttf", "")
    font_base_path = directory / font_family

    def make_variants(font_family, style: str):
        suffixes = [
            style,
            style.capitalize(),
            style.upper(),
        ]
        separators = ["-", "", " ", "_"]
        for sep in separators:
            for suffix in suffixes:
                yield f"{font_family}{sep}{suffix}.ttf"

    fonts = {FontStyle.REGULAR.value: str(font_path)}
    for style in list(FontStyle)[1:]:
        for variant in make_variants(font_family, style.value):
            origin = Path(font_path.parent) / variant
            if origin.exists():
                fonts[style.value] = variant
                break

    toml_dict = {
        font_family: {
            "styles": fonts,
            "origin": {
                "url": str(directory),
                "type": "local_path",
            },
        }
    }

    return toml_dict


def add_local_font(font_path: str):
    d = font_to_toml_dict(font_path)

    if d:
        font_config = load_font_config()
        print("Updating existing config")
        print(font_config)
        print("with ===================")
        print(d)
        print("========================")
        font_config.update(d)
        save_font_config(font_config)


def main():
    parser = argparse.ArgumentParser(description="Font Downloader")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List available fonts")
    group.add_argument("--update-all", action="store_true", help="Update all fonts")
    group.add_argument(
        "--update-font",
        metavar="FONT",
        nargs="+",
        help="Update specific fonts by family name, e.g. 'JetBrainsMono'",
    )
    group.add_argument(
        "--add-local-font",
        metavar="PATH",
        help="Add a font to the configuration given the path to its regular "
        "variant, e.g. '~/Library/Fonts/JetBrainsMono-Regular.ttf'",
    )

    args = parser.parse_args()
    config = load_font_config()

    if args.list:
        list_fonts(config)
    elif args.update_all:
        update_all_fonts(config)
    elif args.update_font:
        update_fonts(config, args.update_font)
    elif args.add_local_font:
        add_local_font(args.add_local_font)


if __name__ == "__main__":
    main()
