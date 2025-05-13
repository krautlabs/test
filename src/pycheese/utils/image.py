from PIL import Image, ImageColor


def create_uniform_background(width, height, color="white"):
    color = any_color_to_rgba(color)
    return Image.new("RGBA", (width, height), color)


def create_gradient_background(width, height, start_color="coral", end_color="salmon"):
    import math

    start_color = any_color_to_rgba(start_color)
    end_color = any_color_to_rgba(end_color)

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


def any_color_to_rgba(color):
    """Converts any color name (str), RGB, or RGBA tuple to RGBA.

    Find a list of colors at https://www.w3.org/TR/css-color-3/#svg-color
    For example, color can be \"skyblue\", (255, 126, 0), or (0, 255, 80, 0).
    """
    if isinstance(color, str):
        try:
            return ImageColor.getcolor(color, "RGBA")
        except ValueError:
            pass

    if isinstance(color, (tuple, list)):
        if len(color) == 3:
            color = tuple(color) + (255,)
        if len(color) == 4:
            if all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                return color

    raise ValueError(
        "Specify a valid color name, hex color, or an RGB/RGBA tuple "
        "with integers in the 0-255 range."
    )
