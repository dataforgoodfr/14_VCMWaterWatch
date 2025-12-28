# Python Workflows

## Python Environment

Install python dependencies:

```bash
uv sync
```

`uv` will create a Python virtual environment.  IDE such as VSCode will usually find that automatically, but you can activate
it manually with:

```bash
source .venv/bin/activate
```

or use `uv` to run commands:

```bash
uv run python
```

The justfile recipes from the top of the repo will do that automatically.

## Configuration

Credentials are configured in the file `.env` at the root of this repository.
Copy from .env.example and update with actual values.

## Running workflows