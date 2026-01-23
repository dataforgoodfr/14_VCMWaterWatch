# VCM Water Watch

## Objectif

Créer une plateforme collaborative et scientifique pour cartographier et analyser les risques de pollution de l’eau par les CVM/VCM dans les tuyaux en PVC installés dans les années 70/80 en Europe. La plateforme permettra de visualiser les risques connus et potentiels, d’identifier les manques de données, et de stimuler la contribution citoyenne et institutionnelle à la recherche.

## Stack Components

 - NocoDB = database frontend
 - 

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

## Python Data Transformations

See [Pipelines Documentation](pipelines/README.md)
