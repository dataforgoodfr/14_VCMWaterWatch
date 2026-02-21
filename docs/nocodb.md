# NocoDB

## What is it

NocoDB is a database frontend.  This gives us a free admin interface for our database object,
including some forms for data entry.

## Local NocoDB

The production data is hosted on DataForGood server.  For development of the web app and
to test ETL scripts, we use a local instance running with Docker.
A sqlite file, with a copy of the database, is shipped with the git repository.
During initial setup (`just setup`), the file is copied to the docker container.

There is no fully automated process to sync data or schema from local to production or vice
versa.  We used a [python script](https://github.com/nicocrm/nocodb_export) for the initial 
export to production and import into local instance, but most changes from that point are handled
manually (by modifying the data locally and committing the modified sqlite file)

To re-run the full export/import:

 * clone [nocodb_export](https://github.com/nicocrm/nocodb_export) to a local folder
 * run the export (replace xxxx with API token):

    NOCODB_URL=https://noco.services.dataforgood.fr \
    BASE_ID=pqc6cnm5mpnr9ka \
    OUTPUT_FILE=vcm_data.json \
    NOCODB_TOKEN=xxxx \
    uv run python nocodb_full_export.py

 * control the generated JSON file
 * run the import (replace with your generated file):

    NOCODB_URL=http://localhost:8500\
    NOCODB_TOKEN= \
    NOCODB_EMAIL=vcmdev@dataforgood.fr \
    NOCODB_PASSWORD=14vcm2026 \
    NEW_BASE_TITLE=14_VCM \
    IMPORT_FILE=vcm_data.json \
    uv run python nocodb_full_import.py

Note, the import process is not optimized and will take a few hours.

## Staging NocoDB

We have a database `14_VCM Staging` that can be used for testing.  It will be occasionally refreshed
from production.  The URL is the same as production, only the `BASE_ID` will be different.

## API

To access the database we use the [REST API](https://nocodb.com/docs/product-docs/developer-resources/rest-apis)
of NocoDB, rather than hitting the underlying database directly.  Both the python and typescript codebases
have a wrapper client.  It's important to note that the field and table ids are not the same in dev and
production and thus must not be hard coded.
