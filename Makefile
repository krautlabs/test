.PHONY: test coverage html clean

# Run tests with pytest
test:
	pytest

# Run coverage and display terminal report
coverage:
	coverage run -m pytest
	coverage report

# Generate and open HTML coverage report
html:
	coverage run -m pytest
	coverage html
	@echo "HTML report generated at htmlcov/index.html"

build:
	hatch build

# Remove coverage files and __pycache__
clean:
	rm -rf .coverage htmlcov dist __pycache__ */__pycache__ .pytest_cache
