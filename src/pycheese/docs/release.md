# Release Process

## Run Tests

```bash
hatch run pytest
```

## Increment Version

Run the following commands to increment the package's `__version__` number in the `__init__.py` file.

```bash
VERSION=0.2.1
hatch version $VERSION

# commit the updated init file
git add -u
git commit -m"bump version to $VERSION"
```

Tag the release to trigger the publication to PyPi.

```bash
git tag v$VERSION
git push origin v$VERSION
```
