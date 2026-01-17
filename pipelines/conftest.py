"""Pytest configuration and shared fixtures."""
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def swagger_file_path(project_root):
    """Return the path to the nocodb swagger file."""
    return project_root / "pipelines" / "common" / "nocodb_swagger.json"


@pytest.fixture
def test_data_dir(project_root):
    """Return the test data directory."""
    return project_root / "data"

