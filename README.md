# PyCheese

[![PyPI](https://img.shields.io/pypi/v/pycheese?logo=pypi&logoColor=white&label=PyPI&color=7934C5)](https://pypi.org/project/pycheese/)
[![Codecov](https://img.shields.io/codecov/c/github/krautlabs/test?logo=codecov&logoColor=white&label=Coverage&color=5D4ED3)](https://app.codecov.io/gh/krautlabs/test)
[![License](https://img.shields.io/github/license/krautlabs/test?logo=opensourceinitiative&logoColor=white&label=License&color=8A2BE2)](https://github.com/krautlabs/test/blob/main/LICENSE)
[![CI All Passed](https://img.shields.io/github/actions/workflow/status/krautlabs/test/ci.yml?label=CI%20All%20Passed&logo=githubactions&logoColor=white&color=2E8B57)](https://github.com/krautlabs/test/actions/workflows/ci.yml)

[![CI: Python 3.11](https://img.shields.io/github/actions/workflow/status/krautlabs/test/test-python-3.11.yml?logo=githubactions&label=Python%203.11&logoColor=white&color=4169E1)](https://github.com/krautlabs/test/actions/workflows/test-python-3.11.yml)
[![CI: Python 3.12](https://img.shields.io/github/actions/workflow/status/krautlabs/test/test-python-3.12.yml?logo=githubactions&label=Python%203.12&logoColor=white&color=4169E1)](https://github.com/krautlabs/test/actions/workflows/test-python-3.12.yml)
[![CI: Python 3.13](https://img.shields.io/github/actions/workflow/status/krautlabs/test/test-python-3.13.yml?logo=githubactions&label=Python%203.13&logoColor=white&color=4169E1)](https://github.com/krautlabs/test/actions/workflows/test-python-3.13.yml)


**PyCheese** is a Python-based tool for generating beautiful, high-quality images of code with syntax highlighting, rendered in a macOS-style terminal window. Built for automation and easy customization, it can be easily integrated into scripts or pipelines.

![example-image](docs/hero_image.png)

---

## Features

- **Syntax Highlighting** – Utilizes [Pygments](https://pygments.org) with support for dozens of languages.
- **MacOS-Style Terminal UI** – Recreates the terminal header and shadow.
- **Fonts** – Comes with JetBrains Mono for elegant, readable code. Use any TTF font.
- **Fully Scriptable** – Designed to run headlessly from scripts, CI pipelines, or other Python apps.
- **Easily Customizable** – Modify themes, fonts, window styles, and more in plain Python.
- **Self-contained** – No need for connectivity and REST calls. Everything runs locally.

---


## Installation & Quickstart

```bash
pip install pycheese
```

Run the following and look at the PNG file.

```bash
echo "import os" | pycheese
```

## Usage

### Command Line

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


### Docker

It's also possible to run the application in an isolated container. First, build the Docker image.

```bash
docker build -t pycheese-app .
```

Then run the application container.

```bash
docker run --rm pycheese-app --help
```

Mount the local directory to allow Docker to read Python files and save image files.

```bash
docker run -v $(pwd):/data --rm pycheese-app --file code.py --output out.png
```


### Python API

The Python API allows more fine-grained control over the end-result by setting the appropiate configuration parameters. First create a `RenderConfig` and then a `Render` object. Then call `.render(code="import os")` on the `Render` object and save the output with `.save_image()`.

```python
from pycheese import *

config = RenderConfig()  # use defaults
render = Render(config)

code = 'print("Hello, world!")'
render.render(code=code)
render.save_image("hello_world.png")
```

Any parameters can be set via the `RenderConfig`. Defaults will be used for the remaining ones.

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


## Layers & Animations

PyCheese renders four distinct layers: background, shadow, text, and title bar. They are composited into the final image. This approach allows the modification of individual layers for an animation without having to re-render any other layers. Each layer can be rendered separately (e.g. `.render_text_layer()`) and retrieved (e.g. `.text_layer`).

- `bg_layer`
- `shadow_layer`
- `text_layer`
- `titlebar_layer`
- `final_image`

It's possible to efficiently generate multiple images or an animation by only modifying the layer that is changing. Here we change the style of the text layer, all the remaining layers remain unchanged and will not get re-rendered when `.render()` is called.

```python
import time
code='print("Hello, world!")'

for style in ["monokai", "dracula"]:
    render.render_text_layer(code=code, style=style)
    render.render()
    render.final_image.show()
    time.sleep(0.5)
```


## Styles

PyCheese uses the Pygments library which comes with a range of styles that can be selected with the `--style` options. The complete list with examples can be found [here](https://pygments.org/styles/).

| Dark Style   | Light Style        |
|--------------|--------------------|
| monokai      | solarized-light    |
| zenburn      | gruvbox-light      |
| nord         | friendly           |
| dracula      | friendly_grayscale |
| gruvbox-dark | murphy             |


## Fonts

The tool comes with the [JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) font. 

> ℹ️ **Note:** Custom font support is experimental. It's recommended to use the default "JetBrainsMono".


To add more fonts, edit the `font_config.toml` file in the `fonts/` directory. And download it with the included `fonts-tool`.

```bash
font-tool --update-font NewFont
```


Once added the font can be selected using its family name, the name excluding regular/bold/italic suffixes and the `.ttf` extension. The included font's family name is `JetBrainsMono` and the family name for the above example is `"MesloLGS NF"`. Check quickly if the new font works by setting the `--font` option.

```bash
echo "import os" | pycheese --font "MesloLGS NF"
```


You can list all available fonts.

```bash
font-tool --list
```

And even add local fonts.

```bash
font-tool --add-local-font ~/Library/Fonts/MesloLGS\ NF\ Regular.ttf
```


## Line Wrapping

Line wrapping is applied to fit content into the limits of the rendered terminal window. Currently, the line wrapping happens at character level and can break up words. To see it in action, run the `linewrap` script directly.

```bash
linewrap --columns 20 tests/sample_code.py
```


## Alternatives

PyCheese is by far not the only way to produce beautiful images of code. (However, it is one of few that can be easily run locally and used for automation.) Here is a small selection of alternatives:

- [Raycast](https://www.ray.so/)
- [codepng](https://www.codepng.app/)
- [Code Beautify](https://codebeautify.org/)
- [Carbon](https://carbon.now.sh)


## Font License

JetBrains Mono typeface is available under the [OFL-1.1 License](https://github.com/JetBrains/JetBrainsMono/blob/master/OFL.txt) and can be used free of charge, for both commercial and non-commercial purposes. You do not need to give credit to JetBrains, although we will appreciate it very much if you do. See [JetBrainsMono License](https://github.com/JetBrains/JetBrainsMono?tab=readme-ov-file#license)


## License

With the exception of the font files, the code and assets contained in this repository are licensed under [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt) as detailed in the `LICENSE` file.
