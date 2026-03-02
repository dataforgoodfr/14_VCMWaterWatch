#!/bin/bash

[ -f data/nocodb/noco.db ] || gunzip -k data/nocodb/noco.db.gz
if [ ! -f .env ]; then
    cat > .env <<EOT
NOCODB_TOKEN=qgM7rqQxsi8OXy8TFdPCgRgwMutL1uTlDff4hCjN
NOCODB_BASE_ID=pae9dl82usu5wvw
NOCODB_URL=http://localhost:8500
EOT
fi
