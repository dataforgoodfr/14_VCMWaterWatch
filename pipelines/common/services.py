from pipelines.common.db_helper import DatabaseHelper
import dotenv
import os


dotenv.load_dotenv()


def db_helper() -> DatabaseHelper:
    """Create a new DatabaseHelper instance."""
    api_token = os.getenv("NOCODB_API_TOKEN")
    if api_token is None:
        raise ValueError("NOCODB_API_TOKEN is not set")

    base_url = os.getenv("NOCODB_URL")
    if base_url is None:
        raise ValueError("NOCODB_URL is not set")

    base_id = os.getenv("BASE_ID")
    if base_id is None:
        raise ValueError("BASE_ID is not set")

    return DatabaseHelper(api_token=api_token, base_url=base_url, base_id=base_id)
