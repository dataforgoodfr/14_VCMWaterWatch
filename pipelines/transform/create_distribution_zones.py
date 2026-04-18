"""
Prefect workflow for creating distribution zones based on water companies and municipalities.
"""

from pathlib import Path
from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import staging_db


@task(name="create_distribution_zones", cache_policy=NO_CACHE)
def create_distribution_zones_task(water_companies: list[dict]) -> list[dict]:
    """
    Create distribution zones based on water companies.
    """
    return [
        {
            "Code": r["Name"],
            "Name": r["Name"],
            "CountryCode": r["CountryCode"],
            "Municipalities": r["Municipalities"],
            "Type": "Distribution",
        }
        for r in water_companies
    ]


@flow(name="create_distribution_zones", persist_result=False)
def create_distribution_zones_flow(data_directory: Path):
    """
    Create distribution zones based on water companies and municipalities.
    """
    conn = staging_db.get_connection(data_directory)
    try:
        # Discover all WaterCompany_* tables in raw schema dynamically
        raw_tables = conn.sql(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'raw' AND table_name LIKE 'WaterCompany_%'"
        ).fetchall()
        table_names = [row[0] for row in raw_tables]

        if not table_names:
            distribution_zones = []
        else:
            union_query = " UNION ALL ".join(
                f'SELECT * FROM raw."{t}"' for t in table_names
            )
            water_companies = conn.sql(union_query).fetchall()
            columns = [desc[0] for desc in conn.description()]
            water_companies = [dict(zip(columns, row)) for row in water_companies]

            distribution_zones = create_distribution_zones_task(water_companies)
        staging_db.write_table(
            conn,
            "DistributionZone_from_water_companies",
            distribution_zones,
            schema="staging",
        )
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python create_distribution_zones.py <data_directory>")
        sys.exit(1)

    data_directory = Path(sys.argv[1])
    create_distribution_zones_flow(data_directory)
