_default:
  @just --list
  @echo ""
  @echo "Run 'just <recipe>' to execute a task."

# install environment and pre-commit hooks
install:
	uv sync
	pre-commit install

# run tests for the Python pipelines
pipelines-test:
	uv run pytest pipelines

mod extract 'pipelines/extract'
mod transform 'pipelines/transform'
mod load 'pipelines/load'
mod task 'pipelines/tasks'