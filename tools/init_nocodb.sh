#!/bin/bash

[ -f data/nocodb/noco.db ] || gunzip -k data/nocodb/noco.db.gz
if [ ! -f .env ]; then
    cat > .env <<EOT
NOCODB_API_TOKEN=qgM7rqQxsi8OXy8TFdPCgRgwMutL1uTlDff4hCjN
NOCODB_URL=http://localhost:8500
EOT
fi
