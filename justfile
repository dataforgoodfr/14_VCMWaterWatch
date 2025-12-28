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
# import-countries:
#   uv run python -m pipelines.load_zones.import_geojson Country data/countries.geojson

# import-municipalities:
#   uv run python -m pipelines.load_zones.download_municipalities
#   uv run python -m pipelines.load_zones.import_geojson Municipality data/municipalities.geojson

# import-water-companies:
#   uv run python -m pipelines.load_water_companies.load_water_companies