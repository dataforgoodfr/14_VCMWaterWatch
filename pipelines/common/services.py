from .db_helper import DatabaseHelper
import dotenv
import os


dotenv.load_dotenv()


def db_helper() -> DatabaseHelper:
    """Create a new DatabaseHelper instance."""
    api_token = os.getenv("NOCODB_API_TOKEN")
    if api_token is None:
        raise ValueError("NOCODB_API_TOKEN is not set")

    return DatabaseHelper(api_token=api_token)
