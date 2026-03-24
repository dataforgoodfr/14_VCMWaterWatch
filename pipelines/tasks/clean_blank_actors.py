from pipelines.common import services
from prefect import flow


@flow(name="clean_actors", persist_result=False)
def clean_actors_flow():
    """
    Delete actors that have a blank name.
    """
    db_helper = services.db_helper()
    records = db_helper.load_all_records(
        table_name="Actor",
        fields=["Name", "Id"],
    )
    to_delete = [r for r in records if r.get("Name") is None]
    db_helper.delete_records(to_delete, table_name="Actor")
    return to_delete


if __name__ == "__main__":
    clean_actors_flow()
