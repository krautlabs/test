# Release Process

## Run Tests

```bash
hatch run pytest
```

## Run Docker Tests

```bash
docker build --target tester -t pycheese-test .
```

## Commit Latest Changes

```bash
git add -u
git commit
```

## Increment Version

Run the following commands to increment the package's `__version__` number in the `__init__.py` file.

```bash
VERSION=0.3.1
hatch version $VERSION

# commit the updated init file
git add src/pycheese/__init__.py
git commit -m"bump version to $VERSION"
```

Tag the release to trigger the publication to PyPi.

```bash
git tag v$VERSION
git push origin main --tags
```

## Environments

The `runtime` environment includes only the dependencies that come with `pip install pycheese`.

```bash
hatch shell runtime
```

An interactive IPython session in the dev (`default`) environment can be started with:

```bash
hatch run default:ipython
```


All other environments will include additional dependencies under `[tool.hatch.envs.default]`.

Environments can be deleted and created with:

```bash
hatch env remove default
hatch env create default
```


## Update Environments

```bash
uv pip compile pyproject.toml --upgrade
```


## Generate documentation

```bash
hatch run docs:mkdocs serve
```


## Generate Hero Image

```bash
pycheese --columns 50 --rows 15 --style dracula \
         --file tests/sample_code.py --output hero_image.png
```


## Run Docker

```bash
docker build -t pycheese-app .
docker run -v $(pwd):/data --rm pycheese-app --file code.py --output out.png
```
