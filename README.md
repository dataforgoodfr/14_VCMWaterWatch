# VCM Water Watch

## Objectif

Créer une plateforme collaborative et scientifique pour cartographier et analyser les risques de pollution de l’eau par les CVM/VCM dans les tuyaux en PVC installés dans les années 70/80 en Europe. La plateforme permettra de visualiser les risques connus et potentiels, d’identifier les manques de données, et de stimuler la contribution citoyenne et institutionnelle à la recherche.

## Stack Components

 - NocoDB = database frontend
 - Next.js = web frontend
 - Python with Prefect and Polars = data transformation scripts

## Local Development Environment

### Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for dependency management
- [just](https://just.systems/) for running tasks
- [pre-commit](https://pre-commit.com/)
- [docker](https://www.docker.com/), recent version

### Installation

```bash
just setup
```

This will install:

 - Python dependencies, using `uv`
 - pre-commit hooks, using `pre-commit`
 - a docker instance with a local copy of NocoDB
 - a default configuration in .env, pointing to the local instance

Then, it will start the local nocodb instance (see [nocodb](docs/nocodb.md)).
You can access it at `http://localhost:8500` - use username "dev@vcmwatch.eu", ask tech leads for password.

To reset the environment:

```bash
just reset
```

## Git Conventions

### Branch Naming

Branches follow the pattern: `<username>/<type>/<issue_number>-<description>`

- `username`: short name identifying the developer (e.g., `nicg`, `juho`)
- `type`: one of `feat`, `bug`, `task`
- `issue_number`: GitHub issue number, when one exists
- `description`: short kebab-case summary

Examples:

- `nicg/feat/21-country-pmtiles`
- `juho/bug/prevent-bug-image-no-signed-url`
- `nicg/task/document_conventions`

### Commit Messages

When a commit is linked to a GitHub issue, use: `#<issue_number> | <description>`

For minor or infrastructure changes without an issue, a plain imperative description is acceptable.

Examples:

- `#24 | database-independant db_helper`
- `#13 | BFF setup for distributionZones search in client component`
- `Add github hook to run python unit tests`

Side note for CLI users: since `#` is the default comment character in Git, to be able to do commit
messages in the CLI you will need to do something like `git config core.commentChar \;`

## Python Data Transformations

See [Pipelines Documentation](pipelines/README.md)
