#!/bin/bash

STAGED_FILES=$(git diff --cached --name-only)

if echo "$STAGED_FILES" | grep -q '^webapp/'; then
  echo "Changes in webapp/ detected, running lint-staged..."
  cd webapp && npx lint-staged
  exit_code=$?
  exit $exit_code
else
  echo "No changes in webapp/ -- skipping lint-staged."
fi