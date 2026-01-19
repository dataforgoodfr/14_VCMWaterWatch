# VCM Water Watch

## Objectif

Créer une plateforme collaborative et scientifique pour cartographier et analyser les risques de pollution de l’eau par les CVM/VCM dans les tuyaux en PVC installés dans les années 70/80 en Europe. La plateforme permettra de visualiser les risques connus et potentiels, d’identifier les manques de données, et de stimuler la contribution citoyenne et institutionnelle à la recherche.

## Contributing

### Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for dependency management
- [just](https://just.systems/) for running tasks
- [pre-commit](https://pre-commit.com/)

### Installation

```bash
just install
```

This will install:

 - Python dependencies, using `uv`
 - pre-commit hooks, using `pre-commit`

### Running Python ETL

See [Pipelines Documentation](pipelines/README.md)