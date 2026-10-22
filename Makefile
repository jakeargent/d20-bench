.PHONY: check build package preview
check:
	uv run python -m unittest discover -s tests -v
	uv run python scripts/publication.py validate
build:
	uv run python scripts/publication.py build
package: check
	uv run python scripts/publication.py package
preview:
	uv run python scripts/publication.py serve
