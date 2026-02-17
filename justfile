_default:
  @just --list
  @echo ""
  @echo "Run 'just <recipe>' to execute a task."

# install environment and pre-commit hooks
setup:
  uv sync
  uvx pre-commit install
  ./tools/init_nocodb.sh
  docker compose up -d

clean:
  docker compose down
  rm -f data/nocodb/noco.db

reset: clean setup
  just setup

# All the python tasks
mod pipelines 'pipelines'
