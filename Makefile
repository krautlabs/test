.PHONY: test coverage html build check-build clean

VERSION := $(shell hatch version)

test: check-hatch
coverage: check-hatch
html: check-hatch
build: check-hatch
check-build: check-hatch

# Check if hatch is installed
check-hatch:
	@command -v hatch >/dev/null 2>&1 || { \
		echo >&2 "Error: Could not find 'hatch'." \
		"Please activate virtual environment and/or install 'hatch'."; \
		exit 1; \
	}

test:
	hatch run pytest

# Run coverage and display terminal report
coverage:
	hatch run coverage run -m pytest
	hatch run coverage report

# Generate and open HTML coverage report
html:
	hatch run coverage run -m pytest
	hatch run coverage html
	@echo "HTML report generated at htmlcov/index.html"

# Build tar and whl artifacts
build:
	hatch build

check-build:
	@echo "\nContents of source distribution (.tar.gz):"
	@tar -tzf dist/pycheese-$$(hatch version).tar.gz
	@echo "\nContents of wheel (.whl):"
	@unzip -l dist/pycheese-$$(hatch version)-py3-none-any.whl | \
	awk 'NR > 3 { print $$4 }' | sed '$$d'

clean:
	rm -rf .coverage htmlcov dist __pycache__ */__pycache__ .pytest_cache
