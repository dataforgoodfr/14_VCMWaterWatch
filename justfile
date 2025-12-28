_default:
  @just --list
  @echo ""
  @echo "Run 'just <recipe>' to execute a task."

# install environment and pre-commit hooks
install:
	uv sync
	pre-commit install

# run tests for the Python pipelines
test:
	uv run pytest pipelines