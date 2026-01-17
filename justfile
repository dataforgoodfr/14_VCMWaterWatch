_default:
  @just --list
  @echo ""
  @echo "Run 'just <recipe>' to execute a task."

# install environment and pre-commit hooks
setup:
  uv sync
  pre-commit install
  ./tools/init_nocodb.sh
  docker compose up -d

reset:
  docker compose down
  rm -f data/nocodb/noco.db
  just setup

mod pipelines 'pipelines'
