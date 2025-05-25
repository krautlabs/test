from PIL import Image, ImageColor


def create_uniform_background(width, height, color="white"):
    # color = any_color_to_rgba(color)
    return Image.new("RGBA", (width, height), Color.from_any_color(color).rgba)


def create_gradient_background(width, height, start_color="coral", end_color="salmon"):
    import math

    start_color = Color.from_any_color(start_color).rgba
    end_color = Color.from_any_color(end_color).rgba

    image = Image.new("RGBA", (width, height))
    angle_rad = math.radians(60)

    # Gradient vector components
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)

    for y in range(height):
        for x in range(width):
            # Project point (x, y) onto gradient direction vector
            projection = x * dx + y * dy
            # Normalize projection to range 0–1
            normalized = (projection - min(0, dx * width + dy * height)) / (
                abs(dx) * width + abs(dy) * height
            )
            normalized = max(0, min(1, normalized))  # Clamp to [0, 1]

            # Interpolate colors
            r = int(start_color[0] * (1 - normalized) + end_color[0] * normalized)
            g = int(start_color[1] * (1 - normalized) + end_color[1] * normalized)
            b = int(start_color[2] * (1 - normalized) + end_color[2] * normalized)

            image.putpixel((x, y), (r, g, b))

    return image


# def any_color_to_rgba(color):
#     """Converts any color name (str), RGB, or RGBA tuple to RGBA.
#
#     Find a list of colors at https://www.w3.org/TR/css-color-3/#svg-color
#     For example, color can be \"skyblue\", (255, 126, 0), or (0, 255, 80, 0).
#     """
#     if isinstance(color, str):
#         try:
#             return ImageColor.getcolor(color, "RGBA")
#         except ValueError:
#             pass
#
#     if isinstance(color, (tuple, list)):
#         if len(color) == 3:
#             color = tuple(color) + (255,)
#         if len(color) == 4:
#             if all(isinstance(c, int) and 0 <= c <= 255 for c in color):
#                 return color
#
#     raise ValueError(
#         "Specify a valid color name, hex color, or an RGB/RGBA tuple "
#         "with integers in the 0-255 range."
#     )
#


class Color:
    def __init__(self, red, green, blue, alpha=255):
        channels = ["red", "green", "blue", "alpha"]
        for name, value in zip(channels, [red, green, blue, alpha]):
            if not (0 <= value <= 255):
                raise ValueError(f"{name} channel {value} outside range [0..255]")

        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha
        self._name = None

    @property
    def rgb(self):
        return (self.red, self.green, self.blue)

    @property
    def rgba(self):
        return (self.red, self.green, self.blue, self.alpha)

    @property
    def hex(self):
        """Returns a CSS hex string, e.g. \"#2366ff\"."""
        return "#{:02x}{:02x}{:02x}".format(*self.rgb)

    @property
    def hexa(self):
        """Returns a CSS hex string, e.g. \"#2366ff\"."""
        return "#{:02x}{:02x}{:02x}{:02x}".format(*self.rgba)

    @property
    def name(self):
        if self._name is None:
            for name in ImageColor.colormap:
                if ImageColor.getrgb(name) == (self.rgb):
                    self._name = name
        return self._name

    def __repr__(self):
        return f"Color({self.red}, {self.green}, {self.blue}, {self.alpha})"

    @classmethod
    def from_str(cls, color_str):
        """Color from name (e.g. \"white\") or hex (e.g. \"#2366ff\")."""
        color = cls(*ImageColor.getrgb(color_str))
        if not color_str.startswith("#") and color_str in ImageColor.colormap:
            color._name = color_str
        return color

    @classmethod
    def from_any_color(cls, color):
        """Color can be a name, hex string, RGB/RGBA tuple, or Color instance."""
        if isinstance(color, cls):
            out_color = cls(color.red, color.green, color.blue, color.alpha)
            out_color._name = color._name
            return out_color
        elif isinstance(color, str):
            return cls.from_str(color)
        elif isinstance(color, tuple):
            if len(color) >= 3:
                return cls(*color[:4])
            else:
                raise ValueError("Tuple must be length 3 (RGB) or 4 (RGBA).")
        else:
            raise TypeError("Unsupported color format.")
