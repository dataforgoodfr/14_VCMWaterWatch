# Agent Instructions

When working an issue, start by making a branch if you are not on the correct one.

## Git Conventions

### Branch Naming

Pattern: `<username>/<type>/<issue_number>-<description>`

- `username`: short name identifying the developer (`nicg` for Nicolas; use your own otherwise)
- `type`: one of `feat`, `bug`, `task`
- `issue_number`: GitHub issue number, when one exists
- `description`: short kebab-case summary

Before creating a branch, check `git branch -a` to see which username prefix
the current user has been using in this repo.

### Commit Messages

When a commit is linked to a GitHub issue: `#<issue_number> | <description>`

Full conventions also live in `README.md` → "Git Conventions".
