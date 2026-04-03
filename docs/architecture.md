# VCM Water Watch — Architecture Overview

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          End Users (Browser)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Next.js Application (webapp/)                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐ │
│  │ Pages (SSR)  │  │ Client Comps │  │ API Routes (BFF)          │ │
│  │ [locale]/*   │  │ MapView,     │  │ /api/distributionzones    │ │
│  │              │  │ SearchBar    │  │ /api/countries/[code]     │ │
│  │              │  │              │  │ /api/geocode              │ │
│  │              │  │              │  │ /api/contribute           │ │
│  │              │  │              │  │ /api/join                 │ │
│  └──────────────┘  └──────┬───────┘  │ /pmtiles/[...path]       │ │
│                           │          └────────────┬──────────────┘ │
│                           │                       │                │
│                      PMTiles         NocoDB REST API (xc-token)    │
│                      Protocol              │                       │
└──────────────────────┬─────────────────────┼───────────────────────┘
                       │                     │
                       ▼                     ▼
          ┌────────────────────┐   ┌─────────────────────┐
          │  PMTiles Files     │   │  NocoDB              │
          │  (data/export/)    │   │  (PostgreSQL-backed)  │
          │                    │   │                       │
          │ • data_countries   │   │ Tables:               │
          │ • data_distribution│   │ • Country             │
          │   _zones           │   │ • DistributionZone    │
          └────────────────────┘   │ • Municipality        │
                       ▲           │ • Actor               │
                       │           │ • Interaction          │
                       │           │ • Template             │
                       │           │ • Analysis             │
                       │           └──────────┬────────────┘
                       │                      │
                       │                      │ NocoDB REST API
                       │                      │
┌──────────────────────┴──────────────────────┴──────────────────────┐
│                  Python Pipelines (pipelines/)                      │
│                       Orchestrated by Prefect                       │
│                                                                     │
│  ┌──────────┐   ┌────────────┐   ┌────────┐   ┌────────────────┐  │
│  │ Extract  │──▶│ Transform  │──▶│  Load  │──▶│ Export         │  │
│  │          │   │            │   │        │   │                │  │
│  │ download │   │ create     │   │ load   │   │ NocoDB→GeoJSON │  │
│  │ _munici… │   │ _distribu… │   │ _zones │   │ →tippecanoe   │  │
│  │ uk_ofwat │   │ geojson    │   │ load   │   │ →PMTiles      │  │
│  │ nl_vewin │   │            │   │ _water │   │                │  │
│  │ de_wass… │   │            │   │ _comp… │   └────────────────┘  │
│  └──────────┘   └────────────┘   └────────┘                       │
│       │               │                                            │
│       ▼               ▼                                            │
│  ┌──────────────────────────┐                                      │
│  │ DuckDB (data/)           │   ┌──────────────────────────────┐   │
│  │ • raw.duckdb             │   │ Tasks (in-DB operations)     │   │
│  │ • staging.duckdb         │   │ • calculate_distribution_zone│   │
│  │                          │   │ • clean_blank_actors         │   │
│  │ In-memory conn ATTACHes  │   │ • build_search_index         │   │
│  │ both as raw.* / staging.*│   └──────────────────────────────┘   │
│  └──────────────────────────┘                                      │
└────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend — Next.js (`webapp/`)

**Framework:** Next.js 16 with App Router, React 19, TypeScript, Tailwind CSS.

**Routing:** Locale-prefixed routes (`/[locale]/map`, `/[locale]/act`, `/[locale]/country-profile`, etc.) with i18next for internationalization.

**Key pages:**
| Route | Purpose |
|---|---|
| `/[locale]/` | Landing page with hero, cards, info sections |
| `/[locale]/map` | Interactive map with PMTiles vector layers |
| `/[locale]/act` | Citizen action page — search zone, download letter templates, submit data |
| `/[locale]/country-profile` | Country detail with carousel |
| `/[locale]/blog/[slug]` | Blog content from NocoDB |
| `/[locale]/resources` | Resources page |

**Map stack:** MapLibre GL JS via `react-map-gl`, with `pmtiles` protocol adapter. Two vector tile sources are loaded from local PMTiles files (countries + distribution zones). The map style is defined in `lib/map/mapStyle.ts`.

#### Backend-for-Frontend (API Routes)

Next.js API routes act as a BFF layer, hiding NocoDB credentials from the browser:

| Route | Role |
|---|---|
| `GET /api/distributionzones` | Returns zones + countries for map overlays |
| `GET /api/countries/[code]` | Country detail by ISO code |
| `GET /api/searchbydistributionzone` | Search zones (for the Act page) |
| `GET /api/distributionzone/[id]` | Single zone detail |
| `GET /api/geocode` | Geocoding proxy (Photon) |
| `POST /api/contribute` | Data submission form |
| `POST /api/join` | Join project form |
| `GET/HEAD /pmtiles/[...path]` | Static PMTiles file server with HTTP Range support |

All NocoDB calls use an Axios instance (`lib/instance.ts`) configured with `NOCODB_URL` and `NOCODB_TOKEN` env vars, targeting the v3 API.

### 2. Database — NocoDB

NocoDB provides a **spreadsheet-like UI** on top of a relational database, used as the primary operational data store. It exposes a REST API consumed by both the Next.js BFF and the Python pipelines.

**Key tables:** Country, DistributionZone, Municipality, Actor, ContactPerson, Interaction, Attachment, Template, Analysis (see `docs/data_model.md` for full ER diagram).

**Access pattern:**
- Frontend reads via API routes (read-only for display)
- Pipelines read/write via `DatabaseHelper` (`pipelines/common/db_helper.py`) using httpx
- Volunteers and project members edit data directly in the NocoDB web UI

### 3. Data Pipelines — Python + Prefect (`pipelines/`)

Orchestrated with **Prefect** (flows + tasks). Each pipeline category corresponds to a stage in the data lifecycle:

#### Extract (`pipelines/extract/`)
Download raw data from external sources into `data/raw/`:
- `download_municipalities` — EU commune geometries (GPKG → GeoJSON)
- `uk_ofwat` — UK water company data from Ofwat
- `nl_vewin` — Dutch water companies from Vewin
- `de_wasserportal` — German water portal data

#### Transform (`pipelines/transform/`)
Process raw data into staging:
- `create_distribution_zones` — Build zone records from water company data
- `geojson` — Geometry processing utilities

#### Load (`pipelines/load/`)
Push staging data into NocoDB:
- `load_zones` — Load distribution zone records
- `load_water_companies` — Load/update actor records with linked zones
- Uses `DatabaseHelper` for NocoDB CRUD operations

#### Export (`pipelines/export/`)
Generate static assets from NocoDB data:
- `export_pmtiles` — Read zones from NocoDB → GeoJSON → PMTiles (via `tippecanoe`)
- Output: `data/export/data_countries.pmtiles`, `data/export/data_distribution_zones.pmtiles`

#### Tasks (`pipelines/tasks/`)
In-database operations on NocoDB data:
- `calculate_distribution_zone` — Compute zone geometries from linked municipalities
- `clean_blank_actors` — Remove empty actor records
- `build_search_index` — Build search index data

### 4. DuckDB (`data/`)

Used as a **local staging database** for the ETL pipelines. Not accessed at runtime by the web application.

- **`data/raw/raw.duckdb`** — Raw extracted data before transformation
- **`data/staging/staging.duckdb`** — Cleaned/transformed data ready for NocoDB load
- Accessed via an in-memory connection that `ATTACH`es both databases (`staging_db.py`)
- Provides SQL capabilities for joins, aggregations during transformation

### 5. PMTiles

[PMTiles](https://protomaps.com/docs/pmtiles) is a **single-file vector tile archive** format, enabling efficient map rendering without a tile server.

**Generation:** The export pipeline reads geometry data from NocoDB, produces GeoJSON, then converts to PMTiles using `tippecanoe`.

**Serving:** The Next.js app serves PMTiles via a custom route handler (`/pmtiles/[...path]`) that supports HTTP Range requests. Files are resolved from `public/pmtiles/` or `data/export/`.

**Consumption:** The MapLibre GL client registers a `pmtiles://` protocol adapter that fetches tile data via Range requests, rendering vector layers for countries and distribution zones directly in the browser.

## Data Flow Summary

```
External Sources (Eurostat, Ofwat, Vewin, ...)
        │
        ▼  [Extract]
    data/raw/ + raw.duckdb
        │
        ▼  [Transform]
    data/staging/ + staging.duckdb
        │
        ▼  [Load]
      NocoDB  ◄──── Manual edits by volunteers
        │
        ├──▶ [Export] ──▶ PMTiles (data/export/)
        │                       │
        │                       ▼
        │               Next.js /pmtiles/* ──▶ MapLibre GL (browser)
        │
        └──▶ Next.js API routes ──▶ Pages (SSR + client components)
```

## Deployment

- **Web app:** Docker container deployed via Coolify to `vcmwaterwatch.services.d4g.fr`
- **NocoDB:** Hosted instance at `noco.services.dataforgood.fr`
- **Pipelines:** Run manually (via `just` commands) or locally by developers
- **Reverse proxy:** Traefik (via Docker labels in `docker-compose.deploy.yml`)
