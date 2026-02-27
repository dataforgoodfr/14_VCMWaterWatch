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

### Windows installation

When installing uv, just and docker, even if corresponding files are added to PATH, Git Bash may not read Windows path correctly. Thus, use:
```bash
nano ~/.bashrc
```
This will open the bashrc file in which you can write:
```bash
export PATH="path/to/your/required/file:$PATH"
# Example:
# export PATH="/c/ProgramData/chocolatey/bin:$PATH"
```
Then press Ctrl+O to write out, Enter to save, and Ctrl+X to exit.
These lines will not be executed when restarting the shell, so type:
```bash
nano ~/.bash_profile
```
to open the bash_profile file, where you can write:
```bash
if [ -f ~/.bashrc ]; then
  . ~/.bashrc
fi
```
Then press Ctrl+O to write out, Enter to save, and Ctrl+X to exit. This will indicate that if bashrc file exists it should be run and will always be executed when starting a new Bash shell.

## Deployment

Pushes to the main branch will be deployed automatically using [Coolify](https://coolify.services.d4g.fr/).
The service is accessible at [vcmwaterwatch.services.d4g.fr](https://vcmwaterwatch.services.d4g.fr).

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
