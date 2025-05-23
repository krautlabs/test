# Release Process

## Test

```bash
hatch run pytest
```

Increment `__version__` number and release tag.


```bash
VERSION=0.2.1
hatch version $VERSION
```

git add -u
git commit -m"version $VERSION"

```bash
git tag v$VERSION
git push origin v$VERSION
```
