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

## Running an import task

To start a workflow for an import task, use the `just` command at the root of the repository.

There are 3 categories:

 - extract: download raw data and process it into the staging directory
 - transform: additional processing of staging data
 - load: load staging data into NocoDB

Run `just` with the corresponding category to get a list, for example `just extract`.
Then run a task by adding the name, for example `just extract download-municipalities`.