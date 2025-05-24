# PyCheese

![GitHub release](https://img.shields.io/github/v/release/krautlabs/test?style=flat-square)
![PyPI version](https://img.shields.io/pypi/v/pycheese?style=flat-square)
![Codecov](https://img.shields.io/codecov/c/github/krautlabs/test?style=flat-square)
![License](https://img.shields.io/github/license/krautlabs/test?style=flat-square)

**PyCheese** is a Python-based tool for generating beautiful, high-quality images of code with syntax highlighting, rendered in a macOS-style terminal window. Built for automation and easy customization, it can be easily integrated into scripts or pipelines.

![example-image](docs/rendered_terminal.png)

---

## Features

- **Syntax Highlighting** – Utilizes [Pygments](https://pygments.org) with support for dozens of languages.
- **macOS-style Terminal UI** – Recreates the terminal header and shadow.
- **Fonts** – Use any TTF font, comes with JetBrains Mono for elegant, readable code.
- **Fully Scriptable** – Designed to run headlessly from scripts, CI pipelines, or other Python apps.
- **Easily Customizable** – Modify themes, fonts, window styles, and more in plain Python.
- **Self-contained** – No need for browsers or servers. Everything runs locally.

---


## Installation

```bash
pip install pycheese
```

Test if the tool works by running the following and looking at the output PNG file.

```bash
echo "import os" | pycheese 
```


## Command Line Usage

Render the code in `sample_code.py` in a default 80x24 window. By default, the window scrolls with the code and only the last 24 rows will be shown if the code does not fit into the window.

```bash
pycheese --file tests/sample_code.py
```

Use the `--columns` and `--rows` options to change the window size.

```bash
pycheese --columns 45 --file tests/sample_code.py
```

Set the `--style` to dracula and save the output to `window.png`.

```bash
pycheese --columns 80 --rows 24 --style dracula \
         --file tests/sample_code.py --output window.png 
```


## Docker

It's also possible to run the application in an isolated container. First, the Docker image needs to be built.

```bash
docker build -t pycheese-app .
```

Then the application can be run easily from within the container.

```bash
docker run --rm pycheese-app --help
```

Mount the local directory to allow the docker container to read Python files and output images.

```bash
docker run -v $(pwd):/data --rm pycheese-app --columns 45 --file code.py --output out.png
```


## Programmatic Usage

```python
from pycheese import *

config = RenderConfig()
render = Render(config)

code = 'print("Hello, world!")'
render.render(code=code)
render.save_image("hello_world.png")
```

A slightly more custom way to call the tool is to create a `RenderConfig` to overwrite specific parameters.

```python
config = RenderConfig(
    rows = 10,
    columns = 30,
    shadow_blur = 10,
    shadow_color = "darkblue",
    shadow_alpha = 80,
    shadow_offset = 40,
    margin = 50,
    first_bg_color = "#775588",
    second_bg_color = "#663355",
)
render = Render(config)

code = 'print("Hello, world!")'
render.render(code=code)
# show the PIL image object directly
render.final_image.show()
```

PyCheese renders four distinct layers: background, shadow, text, and title bar. They are composited into the final image. This approach allows the modification of individual layers for an animation without having to re-render any other layers.

```python
renderer.bg_layer
renderer.shadow_layer
renderer.text_layer
renderer.titlebar_layer
renderer.final_image
```

It's possible to efficiently generate multiple images or an animation by only modifying the layer that is changing. Here we change the style of the text layer, all the remaining layers remain unchanges will not get re-rendered when `.render()` is called.

```python
import time
code='print("Hello, world!")'

for style in ["monokai", "dracula"]:
    render.render_text_layer(code=code, style=style)
    render.render()
    render.final_image.show()
    time.sleep(0.5)
```

## Fonts

The tool comes with the [JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) font. Direct the tool to your fonts folder for more font choices.


## Styles

PyCheese uses the Pygments library which comes with a range of styles that can be selected with the `--style` options. The complete list can be found [here](https://pygments.org/styles/).

Some dark styles:
- monokai
- zenburn
- nord
- dracula
- gruvbox-dark


Some light styles:
- solarized-light
- gruvbox-light
- friendly
- friendly_grayscale
- murphy


## Line Wrapping

The line wrapping can be independently applied using the `linewrap.py` script.

```bash
hatch run python src/pycheese/utils/linewrap.py --columns 20 tests/sample_code.py
```


## Alternatives

- [Raycast](https://www.ray.so/)
- [codepng](https://www.codepng.app/)
- [Code Beautify](https://codebeautify.org/)
- [Carbon](https://carbon.now.sh)


## Font License

JetBrains Mono typeface is available under the [OFL-1.1 License](https://github.com/JetBrains/JetBrainsMono/blob/master/OFL.txt) and can be used free of charge, for both commercial and non-commercial purposes. You do not need to give credit to JetBrains, although we will appreciate it very much if you do. See [JetBrainsMono License](https://github.com/JetBrains/JetBrainsMono?tab=readme-ov-file#license) 


## License

With the exception of the font files, the code and assets contained in this repository are licensed under [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt) as detailed in the `LICENSE` file.
