import polars as pl
from pipelines.common import services
from prefect import flow


@flow(name="clean_actors", persist_result=False)
def clean_actors_flow():
    """
    Delete actors that have a blank name.
    """
    db_helper = services.db_helper()
    df = db_helper.load_all_records(
        table_name="Actor",
        fields=["Name", "Id"],
    )
    df = df.filter(pl.col("Name").is_null())
    db_helper.delete_records(df, table_name="Actor")
    return df


if __name__ == "__main__":
    clean_actors_flow()
