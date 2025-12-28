Scripts to download and parse raw data into the data/staging folder.

# geojson

Workflow to process .geojson file(s) into data ready to be loaded into the database, with fields:

 - Code
 - Name
 - Geometry
 - ParentCode

# de_wasserportal

Workflow to download data from wasserportal API, to try and match municipalities.
Produces file raw/WaterCompany_de_wasserportal.ndjson with fields:

 - Name
 - Phone
 - Email
 - Website
 - Description
 - Source (set to WasserPortal)
 - Municipalities (array)