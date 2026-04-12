# NocoDB

## What is it

NocoDB is a database frontend.  This gives us a free admin interface for our database object,
including some forms for data entry.

## Local NocoDB

The production data is hosted on the web server at LWS.  For development of the web app and
to test ETL scripts, we use a local instance running with Docker.  This is not included in the repo.
Ask tech leads for a recent database backup.

## API

To access the database we use the [REST API](https://nocodb.com/docs/product-docs/developer-resources/rest-apis)
of NocoDB, rather than hitting the underlying database directly.  Both the python and typescript codebases
have a wrapper client.  It's important to note that the field and table ids are not the same in dev and
production and thus must not be hard coded.
